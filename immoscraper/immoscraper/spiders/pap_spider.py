import scrapy
from immoscraper.items import BuildingType, PropertyAdItem, EnergyConsumption, GES

class PapSpider(scrapy.Spider):
    name = "pap"
    allowed_domains = ["pap.fr"]

    REGION_SLUGS = [
        "guadeloupe-971-g91", "martinique-972-g93", "guyane-973-g94",
        "la-reunion-974-g95", "mayotte-976-g97", "bretagne-g465",
        "centre-val-de-loire-g466", "corse-g468", "ile-de-france-g471",
        "pays-de-la-loire-g477", "provence-alpes-cote-d-azur-g480",
        "normandie-g53044", "grand-est-g53190", "hauts-de-france-g53191",
        "bourgogne-franche-comte-g53197", "occitanie-g64309",
        "nouvelle-aquitaine-g64310", "auvergne-rhone-alpes-g64311"
    ]

    def start_requests(self):
        for mode in ("vente", "location"):
            for slug in self.REGION_SLUGS:
                url = f"https://www.pap.fr/annonce/{mode}-appartement-maison-{slug}"
                yield scrapy.Request(
                    url,
                    callback=self.parse_listing,
                    meta={"mode": mode, "slug": slug, "page_num": 1}
                )

    def parse_listing(self, response):
        mode = response.meta["mode"]
        slug = response.meta["slug"]
        page_num = response.meta["page_num"]

        self.logger.info(f"[LIST] {response.url} (page {page_num})")

        # Extracting announcement cards
        cards = response.css("div.search-list-item-alt")
        found = False
        for card in cards:
            href = card.css("a.item-title::attr(href)").get()
            if href:
                found = True
                yield response.follow(
                    href,
                    callback=self.parse_detail,
                    meta={"mode": mode}
                )

        # Pagination: page 2 and beyond
        # We continue if we found announcements (or if page 1 to try page 2)
        if (found or page_num == 1) and page_num < 50:
            next_page = page_num + 1
            next_url = (
                f"https://www.pap.fr/pagination/"
                f"{mode}-appartement-maison-{slug}-{next_page}"
            )
            self.logger.info(f"→ next page {next_page}: {next_url}")
            yield scrapy.Request(
                next_url,
                callback=self.parse_listing,
                meta={"mode": mode, "slug": slug, "page_num": next_page}
            )
        elif not found and page_num > 1:
            self.logger.info(f"No items on page {page_num}; stop pagination for {slug} {mode}.")

    def parse_detail(self, response):
        item = PropertyAdItem()
        item["url"] = response.url

        # Building type
        typ = response.css("div.ad-details .breadcrumb li:last-child::text").get(default="").strip().lower()
        if "maison" in typ:
            item["building_type"] = BuildingType.HOUSE.value
        elif "appartement" in typ:
            item["building_type"] = BuildingType.APARTMENT.value
        else:
            item["building_type"] = BuildingType.OTHER.value

        # Sale or rent
        item["is_rent"] = (response.meta.get("mode") == "location")

        # Price
        price_txt = response.css("span.ad-price::text").re_first(r"([\d\s\.,]+)")
        if price_txt:
            cleaned = price_txt.replace("\xa0", "").replace(" ", "").replace(",", ".")
            try:
                item["price"] = float(cleaned)
            except ValueError:
                self.logger.error(f"Invalid price '{cleaned}' on {response.url}")
                item["price"] = 0.0
        else:
            item["price"] = 0.0

        # Area
        area_txt = response.css("li.surface span.value::text").re_first(r"([\d\.]+)")
        item["area"] = float(area_txt) if area_txt else 0.0

        # Number of rooms
        rooms_txt = response.css("li.pieces span.value::text").re_first(r"(\d+)")
        item["rooms_count"] = int(rooms_txt) if rooms_txt else None

        # GPS coordinates
        lat = response.css("div.ad-map::attr(data-lat)").get()
        lng = response.css("div.ad-map::attr(data-lng)").get()
        item["latitude"] = float(lat) if lat else None
        item["longitude"] = float(lng) if lng else None

        # DPE / GES
        dpe_txt = response.css("li.dpe span.value::text").get()
        ges_txt = response.css("li.ges span.value::text").get()
        item["energy_consumption"] = (
            EnergyConsumption[dpe_txt.strip()].value
            if dpe_txt and dpe_txt.strip() in EnergyConsumption.__members__
            else EnergyConsumption.NS.value
        )
        item["ges"] = (
            GES[ges_txt.strip()].value
            if ges_txt and ges_txt.strip() in GES.__members__
            else GES.NS.value
        )

        # Metadata
        item["city_insee_code"] = response.css("meta[name=insee]::attr(content)").get(default="")
        item["publication_date"] = response.css("time.ad-date::attr(datetime)").get(default="")

        yield item
