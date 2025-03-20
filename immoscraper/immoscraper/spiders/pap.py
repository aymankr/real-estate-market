from scrapy.spiders import Spider
from immoscraper.items import PropertyAdItem


class Pap(Spider):
    name = "pap"
    
    start_urls = ["https://www.asparton.com/"]
    
    def parse(self, response):
        dummy_item = PropertyAdItem(
            building_type="HOUSE",
            is_rent=False,
            price=1000000,
            area=100,
            latitutde=48.8566,
            longitude=2.3522,
            rooms_count=5,
            energy_consumption="A",
            ges="A",
        )
        yield dummy_item
