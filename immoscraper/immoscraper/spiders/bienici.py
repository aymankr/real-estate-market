import json
import scrapy
import datetime
import logging
from ..items import PropertyAdItem, EnergyConsumption, GES
from ..utils import BuildingTypeConverter
from .data_extractors import PropertyDataExtractor
from .url_builder import BienIciUrlBuilder

class BienIciSpider(scrapy.Spider):
    name = 'bienici'
    allowed_domains = ['bienici.com']
    
    def __init__(self, property_type='all', transaction_type='all', location='france', max_pages=None, *args, **kwargs):
        super(BienIciSpider, self).__init__(*args, **kwargs)
        
        self.max_pages = int(max_pages) if max_pages else None # number of pages to scrape (None = all)
        self.page_size = 24 # number of ads per page
        
        self.transaction_type = transaction_type # buy or rent
        self.filter_type = self._get_filter_type(transaction_type) # property type filter
        
        self.property_type = property_type # house, apartment, etc.
        self.building_types = self._get_building_types(property_type) # list of building types
        
        self.location = location # country (FR)
        
        self.logger.info(f"Initialized BienIci spider with page_size={self.page_size}, max_pages={self.max_pages}")
    
    def _get_filter_type(self, transaction_type):
        """Convert transaction type to filter type"""
        if transaction_type == 'buy':
            return 'buy'
        elif transaction_type == 'rent':
            return 'rent'
        return None
    
    def _get_building_types(self, property_type):
        """Convert property type parameter to building types list"""
        if property_type == 'house':
            return ["house"]
        elif property_type == 'apartment':
            return ["flat"]
        return ["house", "flat", "loft", "castle", "townhouse"]
    
    def start_requests(self):
        """Entry point for the spider"""
        self.logger.info(f"Starting BienIci spider for {self.transaction_type} - {self.property_type} - {self.location}")
        
        url = BienIciUrlBuilder.build_url(
            self.filter_type,
            self.building_types,
            self.page_size,
            1,  # page_number
            0   # start_index
        )
        
        yield scrapy.Request(
            url=url,
            callback=self.parse_listings,
            meta={'page': 1},
            dont_filter=True
        )
    
    def parse_listings(self, response):
        """Parse response for property listings"""
        page_number = response.meta['page']
        
        try:
            data = json.loads(response.text)
            
            total_count = data.get('total', 0)
            listings = data.get('realEstateAds', [])
            
            self.logger.info(f"Page {page_number}: {len(listings)} ads / {total_count} total")
            
            # Process each listing on this page
            for listing in listings:
                listing_id = listing.get('id')
                
                if not listing_id:
                    self.logger.warning("Ad without ID found, skipped")
                    continue
                
                detail_url = BienIciUrlBuilder.build_detail_url(listing_id)
                
                meta_data = {'basic_data': listing}
                if 'district' in listing and isinstance(listing['district'], dict):
                    meta_data['district'] = listing['district']
                
                yield scrapy.Request(
                    url=detail_url,
                    callback=self.parse_listing_details,
                    meta=meta_data
                )
            
            # Pagination: while the page is full, go to the next one
            if listings and (
                len(listings) == self.page_size and 
                (self.max_pages is None or page_number < self.max_pages)
            ):
                next_page = page_number + 1
                start_index = (next_page - 1) * self.page_size
                
                self.logger.info(f"→ Page {next_page} (from={start_index})")
                
                next_url = BienIciUrlBuilder.build_url(
                    self.filter_type,
                    self.building_types,
                    self.page_size,
                    next_page,
                    start_index
                )
                
                yield scrapy.Request(
                    url=next_url,
                    callback=self.parse_listings,
                    meta={'page': next_page},
                    dont_filter=True
                )
            else:
                self.logger.info("No more pages to scrape.")
            
        except json.JSONDecodeError:
            self.logger.error(f"Error decoding JSON response: {response.text[:200]}…")
        except Exception as e:
            self.logger.error(f"Error processing page {page_number}: {e}")


    def parse_listing_details(self, response):
        """Parse property ad details"""
        try:
            basic_data = response.meta.get('basic_data', {})
            district_data = response.meta.get('district', {})
            
            detail_data = json.loads(response.text)
            
            # Get the building type from the response
            property_type = detail_data.get('propertyType')
            building_type = BuildingTypeConverter.from_bienici_type(property_type)
            
            # Get energy classification and convert to enum if present
            energy_class = detail_data.get('energyClassification')
            energy_consumption = None
            if energy_class and len(energy_class) > 0:
                # Take first character (A-G) and convert to enum
                energy_class_letter = energy_class[0].upper()
                if energy_class_letter in "ABCDEFG":
                    energy_consumption = EnergyConsumption(energy_class_letter)
            
            # Get greenhouse gas classification and convert to enum if present
            ges_class = detail_data.get('greenhouseGazClassification')
            ges = None
            if ges_class and len(ges_class) > 0:
                # Take first character (A-G) and convert to enum
                ges_class_letter = ges_class[0].upper()
                if ges_class_letter in "ABCDEFG":
                    ges = GES(ges_class_letter)
            
            # Extract coordinates
            lat, lon = PropertyDataExtractor.extract_coordinates(detail_data, basic_data, 
                      PropertyDataExtractor.extract_insee_code(detail_data, basic_data, district_data))
            
            # Extract city_insee_code
            city_insee_code = PropertyDataExtractor.extract_insee_code(detail_data, basic_data, district_data)
            
            # Publication date
            if 'publicationDate' in detail_data and detail_data['publicationDate'] != "1970-01-01T00:00:00.000Z":
                publication_date = detail_data['publicationDate']
            else:
                publication_date = datetime.datetime.now().isoformat()
            
            # Create the item
            item = PropertyAdItem(
                building_type=building_type,
                is_rent=detail_data.get('transactionType') == 'rent',
                price=float(detail_data.get('price', 0)),
                area=float(detail_data.get('surfaceArea', 0)),
                latitude=float(lat) if lat is not None else None,
                longitude=float(lon) if lon is not None else None,
                rooms_count=int(detail_data.get('roomsQuantity')) if detail_data.get('roomsQuantity') is not None else None,
                energy_consumption=energy_consumption,
                ges=ges,
                city_insee_code=city_insee_code,
                publication_date=publication_date
            )
            
            return item
            
        except json.JSONDecodeError:
            self.logger.error(f"Error decoding JSON detail response: {response.text[:200]}...")
        except Exception as e:
            listing_id = response.meta.get('basic_data', {}).get('id', 'unknown')
            self.logger.error(f"Error processing details for ad {listing_id}: {str(e)}")
            return None 