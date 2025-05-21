import json
import scrapy
from datetime import datetime
from urllib.parse import quote
from ..items import PropertyAdItem, EnergyConsumption, GES
from ..utils import BuildingTypeConverter

class BienIciSpider(scrapy.Spider):
    name = 'bienici'
    allowed_domains = ['bienici.com']
    BASE_URL    = 'https://www.bienici.com/realEstateAds.json'
    DETAIL_URL  = 'https://www.bienici.com/realEstateAd.json'

    def __init__(self,
                 property_type: str    = 'all',
                 transaction_type: str = 'all',
                 location: str         = 'france',
                 max_pages: str | None = None,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.property_type   = property_type
        self.transaction_type= transaction_type
        self.filter_type     = self._get_filter_type(transaction_type)
        self.building_types  = self._get_building_types(property_type)
        self.page_size       = 24
        self.max_pages       = int(max_pages) if max_pages else None
        self.location        = location
        self.logger.info(
            f"Initialized BienIci spider: transaction={transaction_type}, "
            f"property={property_type}, page_size={self.page_size}, max_pages={self.max_pages}"
        )

    def _get_filter_type(self, t: str) -> str | None:
        return {'buy':'buy','rent':'rent'}.get(t)

    def _get_building_types(self, p: str) -> list[str]:
        if p == 'house':     return ['house']
        if p == 'apartment': return ['flat']
        return ['house','flat','loft','castle','townhouse']

    def start_requests(self):
        yield self._list_request(page=1, start=0)

    def _list_request(self, page: int, start: int) -> scrapy.Request:
        filters = {
            'size':         self.page_size,
            'from':         start,
            'filterType':   self.filter_type,
            'propertyType': self.building_types,
            'page':         page,
            'sortBy':       'relevance',
            'sortOrder':    'desc',
            'onTheMarket':  [True],
        }
        # drop None values
        filters = {k: v for k, v in filters.items() if v is not None}
        qs = json.dumps(filters, separators=(',', ':'))
        url = (
            f"{self.BASE_URL}"
            f"?filters={quote(qs)}"
            f"&extensionType=extendedIfNoResult"
            f"&enableGoogleStructuredDataAggregates=true"
        )
        return scrapy.Request(
            url=url,
            callback=self.parse_listings,
            errback=self._errback,
            meta={'page': page, 'start': start},
            dont_filter=True
        )

    def parse_listings(self, response):
        page  = response.meta['page']
        start = response.meta['start']
        try:
            data     = json.loads(response.text)
            listings = data.get('realEstateAds', [])
            total    = data.get('total', 0)
            self.logger.info(f"Page {page}: {len(listings)} ads / {total} total")

            for listing in listings:
                lid = listing.get('id')
                if not lid:
                    continue
                detail_url = f"{self.DETAIL_URL}?id={lid}"
                yield scrapy.Request(
                    url=detail_url,
                    callback=self.parse_detail,
                    errback=self._errback,
                    meta={'basic': listing},
                )

            # next page?
            if listings and len(listings) == self.page_size \
               and (self.max_pages is None or page < self.max_pages):
                next_page  = page + 1
                next_start = start + self.page_size
                self.logger.info(f"→ Page {next_page} (from={next_start})")
                yield self._list_request(next_page, next_start)
            else:
                self.logger.info("No more pages to scrape.")

        except Exception as e:
            self.logger.error(f"Error parsing listings page {page}: {e}")

    def parse_detail(self, response):
        basic  = response.meta.get('basic', {})
        try:
            detail = json.loads(response.text)

            # building type
            btype = detail.get('propertyType')
            building = BuildingTypeConverter.from_bienici_type(btype)

            # transaction
            is_rent = detail.get('transactionType') == 'rent'

            # price
            price = float(detail.get('price', 0))

            # area
            area = float(detail.get('surfaceArea', 0))

            # rooms
            rooms = detail.get('roomsQuantity')

            # energy
            ec = detail.get('energyClassification') or ''
            energy = None
            if ec and ec[0].upper() in "ABCDEFG":
                energy = EnergyConsumption(ec[0].upper())

            # GES
            gg = detail.get('greenhouseGazClassification') or ''
            ges = None
            if gg and gg[0].upper() in "ABCDEFG":
                ges = GES(gg[0].upper())

            # coords
            lat = lon = None
            # 1) blurInfo in detail
            bi = detail.get('blurInfo', {}).get('position')
            if bi and 'lat' in bi and 'lon' in bi:
                lat, lon = bi['lat'], bi['lon']
            # 2) coordinates field
            elif isinstance(detail.get('coordinates'), dict):
                coord = detail['coordinates']
                lat, lon = coord.get('lat'), coord.get('lng')
            # 3) blurInfo in basic
            else:
                bi2 = basic.get('blurInfo', {}).get('position')
                if bi2 and 'lat' in bi2 and 'lon' in bi2:
                    lat, lon = bi2['lat'], bi2['lon']

            # insee/postal
            insee = (
                detail.get('postalCode')
                or detail.get('address', {}).get('postalCode', '')
            )

            # publication date
            pub = detail.get('publicationDate')
            if not pub or pub.startswith('1970'):
                pub = datetime.utcnow().isoformat()

            yield PropertyAdItem(
                building_type      = building,
                is_rent            = is_rent,
                price              = price,
                area               = area,
                latitude           = float(lat) if lat is not None else None,
                longitude          = float(lon) if lon is not None else None,
                rooms_count        = int(rooms) if rooms is not None else None,
                energy_consumption = energy,
                ges                = ges,
                city_insee_code    = insee,
                publication_date   = pub
            )

        except Exception as e:
            lid = basic.get('id', 'unknown')
            self.logger.error(f"Error parsing detail for {lid}: {e}")

    def _errback(self, failure):
        self.logger.error(f"Request failed: {failure.value}", exc_info=False)
