import json
import urllib.parse

class BienIciUrlBuilder:
    """Build URLs for BienIci scraper"""
    
    @staticmethod
    def _build_filters(filter_type, building_types, page_number, page_size, start_index):
        """Build filters for the search"""
        filters = {
            'size': page_size, # number of ads per page
            'from': start_index, # offset (ex: 0, 24, 48...)
            'filterType': filter_type, # property type filter (buy or rent)
            'propertyType': building_types, # list of building types (house, flat, loft, castle, townhouse, etc.)
            'page': page_number, # page number
            'sortBy': "relevance", # sort by relevance
            'sortOrder': "desc", # sort order
            'onTheMarket': [True]
        }
        
        # Remove None values
        return {k: v for k, v in filters.items() if v is not None}
    
    @staticmethod
    def build_url(filter_type, building_types, page_size, page_number, start_index):
        """Build URL for property listings with pagination"""
        base_url = "https://www.bienici.com/realEstateAds.json"
        
        filters = BienIciUrlBuilder._build_filters(
            filter_type, building_types, page_number, page_size, start_index
        )
        
        # Convert filters to JSON string
        filters_json = json.dumps(filters, separators=(',',':')) 
        # Encode filters to URL format
        filters_param = urllib.parse.quote(filters_json)
        
        return f"{base_url}?filters={filters_param}&extensionType=extendedIfNoResult&enableGoogleStructuredDataAggregates=true"
    
    @staticmethod
    def build_detail_url(ad_id):
        """Build URL to get property details"""
        return f"https://www.bienici.com/realEstateAd.json?id={ad_id}"
    
    @staticmethod
    def build_geocoding_url(city, insee_code):
        """Build URL for geocoding API"""
        query = f"{city}-{insee_code}"
        params = {
            "q": query,
            "type": "city,delegated-city,department,postalCode,region",
            "prefix": "no"
        }
        base_url = "https://res.bienici.com/place.json"
        query_string = urllib.parse.urlencode(params)
        return f"{base_url}?{query_string}" 