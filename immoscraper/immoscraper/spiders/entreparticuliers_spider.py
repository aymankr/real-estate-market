import scrapy
import json
from urllib.parse import urlencode
from ..items import PropertyAdItem
from ..utils import BuildingTypeConverter, BuildingType

class EntreParticuliersSpider(scrapy.Spider):
    name = "entreparticuliers"
    allowed_domains = ["api-prod.entreparticuliers.com", "entreparticuliers.com"]

    # WARNING !
    # ASK FOR AUTHORIZATION 
    BASE_URL = "https://api-prod.entreparticuliers.com/api" 
    DEPARTEMENTS_ENDPOINT = f"{BASE_URL}/departements"
    ANNONCES_ENDPOINT = f"{BASE_URL}/annonces"

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/136.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Origin": "https://www.entreparticuliers.com",
        "Referer": "https://www.entreparticuliers.com/",
    }

    def start_requests(self):
        """
        Fetch all French departments to begin crawling ads nationwide.
        """
        params = {
            "pagination": "true",
            "itemsPerPage": 200,
            "page": 1,
            "partial": "true",
        }
        url = f"{self.DEPARTEMENTS_ENDPOINT}?{urlencode(params)}"
        yield scrapy.Request(
            url,
            headers=self.HEADERS,
            callback=self.parse_departements,
            errback=self._errback
        )

    def parse_departements(self, response):
        if response.status != 200:
            self.logger.error(f"Failed to fetch departments: HTTP {response.status}")
            return
        data = response.json()
        for dep in data.get("hydra:member", []):
            dep_uri = f"/api/departements/{dep['id']}"
            # start first page for this department
            yield from self._list_requests_for(dep_uri, page=1)

    def _list_requests_for(self, dep_uri: str, page: int):
        """
        Generate a paginated request for both sale and rental, houses and apartments.
        """
        params = {
            "pagination": "true",
            "itemsPerPage": 12,
            "page": page,
            "partial": "true",
            "commune.departement": dep_uri,
            "estActive": "true",
            "estRefusee": "false",
            "order[date]": "desc",
            # fetch both rentals and sales
            "rubrique[]": ["/api/rubriques/1", "/api/rubriques/2"],
            # fetch both apartments and houses
            "bienType[]": ["/api/bien_types/1", "/api/bien_types/2"],
            "groups[]": "annonce:resultat",
        }
        qs = urlencode(params, doseq=True)
        url = f"{self.ANNONCES_ENDPOINT}?{qs}"
        yield scrapy.Request(
            url,
            headers=self.HEADERS,
            callback=self.parse_listings,
            errback=self._errback,
            meta={"dep_uri": dep_uri, "page": page},
            dont_filter=True
        )

    def parse_listings(self, response):
        dep_uri = response.meta["dep_uri"]
        page = response.meta["page"]

        if response.status == 404:
            # no more pages for this department
            return
        if response.status != 200:
            self.logger.warning(f"Failed to fetch listings {dep_uri} p{page}: HTTP {response.status}")
            return

        data = response.json()
        for raw in data.get("hydra:member", []):
            yield PropertyAdItem(**self._extract_item(raw))

        # follow next page if available
        view = data.get("hydra:view", {})
        next_rel = view.get("hydra:next")
        if next_rel:
            next_url = f"{self.BASE_URL}{next_rel}"
            yield scrapy.Request(
                next_url,
                headers=self.HEADERS,
                callback=self.parse_listings,
                errback=self._errback,
                meta={"dep_uri": dep_uri, "page": page + 1},
                dont_filter=True
            )

    def _extract_item(self, raw: dict) -> dict:
        # building type mapping
        label = raw.get("bienType", {}).get("label", "").strip().lower()
        if label == "maison":
            building = BuildingType.HOUSE
        elif label == "appartement":
            building = BuildingType.APARTMENT
        else:
            building = BuildingTypeConverter.from_bienici_type(label)

        # sale vs rent
        is_rent = raw.get("rubrique", {}).get("slug") == "location"

        # price and area
        price = float(raw.get("prix") or 0)
        area = float(raw.get("surface") or 0)

        # coordinates
        lat = raw.get("latitude")
        lon = raw.get("longitude")

        # rooms count
        rooms = raw.get("piecesnb")
        try:
            rooms = int(rooms) if rooms is not None else None
        except Exception:
            rooms = None

        # energy & GES from detail if present
        # detail = raw.get("detail", {}) or {}
        # energy = detail.get("dpe")
        # ges = detail.get("ges")
        energy, ges = None, None

        # city insee code (postal code)
        city = raw.get("commune", {}).get("codePostal")

        # publication date
        pub = raw.get("date")

        return {
            "building_type": building,
            "is_rent": is_rent,
            "price": price,
            "area": area,
            "latitude": lat,
            "longitude": lon,
            "rooms_count": rooms,
            "energy_consumption": energy,
            "ges": ges,
            "city_insee_code": city,
            "publication_date": pub,
        }

    def _errback(self, failure):
        self.logger.error(f"Request error: {failure.value}")
