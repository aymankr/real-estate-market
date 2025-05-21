import scrapy
import json
import re
from datetime import datetime
from ..items import PropertyAdItem, EnergyConsumption, GES
from ..utils import BuildingTypeConverter, LOGIC_IMMO_PLACE_IDS

class LogicImmoSpider(scrapy.Spider):
    name = "logic_immo"
    allowed_domains = ["logic-immo.com"]

    SEARCH_URL = "https://www.logic-immo.com/serp-bff/search"
    DETAIL_URL = "https://www.logic-immo.com/classifiedList/"

    HEADERS = {
        "User-Agent":       "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/136.0.0.0 Safari/537.36",
        "Accept":           "application/json, text/plain, */*",
        "Accept-Language":  "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Content-Type":     "application/json; charset=utf-8",
        "Origin":           "https://www.logic-immo.com",
        "Referer":          "https://www.logic-immo.com/classified-search",
        "X-Requested-With": "XMLHttpRequest",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.page_size    = 25
        self.max_pages    = None
        self.dist_types   = ["Buy", "Buy_Auction", "Rent"]
        self.estate_types = ["House", "Apartment"]

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        spider.place_ids = LOGIC_IMMO_PLACE_IDS
        return spider

    def start_requests(self):
        yield self._search_request(page=1)

    def _search_request(self, page: int) -> scrapy.Request:
        body = {
            "criteria": {
                "distributionTypes": self.dist_types,
                "estateTypes":       self.estate_types,
                "location":          {"placeIds": self.place_ids},
            },
            "paging": {"page": page, "size": self.page_size, "order": "Default"},
        }
        return scrapy.Request(
            url=self.SEARCH_URL,
            method="POST",
            headers=self.HEADERS,
            body=json.dumps(body, separators=(",", ":")),
            callback=self.parse_search,
            errback=self._errback,
            meta={"page": page, "handle_httpstatus_all": True},
        )

    def parse_search(self, response):
        page = response.meta["page"]
        if response.status != 200:
            self.logger.warning(f"search page {page} returned {response.status}, skipping")
            return

        data = response.json()
        ids  = [c["id"] for c in data.get("classifieds", [])]
        if not ids:
            return

        # fetch details
        yield scrapy.Request(
            url=f"{self.DETAIL_URL}{','.join(ids)}",
            headers=self.HEADERS,
            callback=self.parse_details,
            errback=self._errback,
            meta={"page": page, "handle_httpstatus_all": True},
        )

        # pagination
        if len(ids) == self.page_size and (self.max_pages is None or page < self.max_pages):
            yield self._search_request(page + 1)

    def parse_details(self, response):
        if response.status != 200:
            self.logger.warning(f"details page [{response.meta.get('page')}] returned {response.status}, skipping")
            return
        raws = response.json()
        if not isinstance(raws, list):
            raws = [raws]
        for raw in raws:
            item_data = self._extract_item(raw)
            yield PropertyAdItem(**item_data)

    def _extract_item(self, raw: dict) -> dict:
        rd = raw.get("rawData", {})

        # 1) building_type
        btype = rd.get("propertyType")
        building = BuildingTypeConverter.from_bienici_type(btype)

        # 2) is_rent
        is_rent = rd.get("distributionType", "").upper() == "RENT"

        # 3) price
        pf = raw.get("hardFacts", {}).get("price", {}) or {}
        aria = pf.get("ariaLabel", "")
        if aria:
            # extract digits and dots
            price = float(re.sub(r"[^\d\.]", "", aria.replace(",", ".")))
        else:
            price = float(rd.get("price", 0))

        # 4) area — strip NBSP and other non-digits before float
        area = None
        for fact in raw.get("hardFacts", {}).get("facts", []):
            if fact.get("type") == "livingSpace":
                sv = fact.get("splitValue", "")
                # remove non-digit, non-dot, non-comma, then comma→dot
                cleaned = re.sub(r"[^\d,\.]", "", sv)
                cleaned = cleaned.replace(",", ".")
                try:
                    area = float(cleaned)
                except ValueError:
                    area = None
                break

        # 5) latitude & longitude — TODO
        lat = lon = None

        # 6) rooms_count
        rooms = None
        for fact in raw.get("hardFacts", {}).get("facts", []):
            if fact.get("type") == "numberOfRooms":
                try:
                    rooms = int(fact.get("splitValue", "0"))
                except ValueError:
                    rooms = None
                break

        # 7) energy_consumption
        ec = raw.get("energyClass")
        energy = EnergyConsumption(ec) if ec else None

        # 8) ges
        ges_letter = raw.get("legacyTracking", {}).get("energy_letter")
        ges = GES(ges_letter) if ges_letter else None

        # 9) city_insee_code
        insee = raw.get("location", {}).get("address", {}).get("zipCode", "")

        # 10) publication_date
        pub = raw.get("metadata", {}).get("creationDate")
        if not pub or pub.startswith("1970"):
            pub = datetime.utcnow().isoformat()

        return {
            "building_type":      building,
            "is_rent":            is_rent,
            "price":              price,
            "area":               area,
            "latitude":           lat,
            "longitude":          lon,
            "rooms_count":        rooms,
            "energy_consumption": energy,
            "ges":                ges,
            "city_insee_code":    insee,
            "publication_date":   pub,
        }

    def _errback(self, failure):
        self.logger.error(f"Request failed: {failure.value}", exc_info=False)
