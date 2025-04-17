import json
import urllib.parse

class BienIciUrlBuilder:
    """Build URLs for BienIci scraper"""
    
    @staticmethod
    def build_search_url(filter_type, building_types, page_size=24):
        """Build the base search URL for BienIci scraper with filters"""
        base_url = "https://www.bienici.com/realEstateAds.json"
        
        filters = {
            'size': page_size,
            'from': 0,
            'showAllModels': False,
            'filterType': filter_type,
            'propertyType': building_types,
            'page': 1,
            'sortBy': "relevance",
            'sortOrder': "desc",
            'onTheMarket': [True]
        }
        
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}
        
        filters_json = json.dumps(filters)
        filters_param = urllib.parse.quote(filters_json)
        
        return f"{base_url}?filters={filters_param}&extensionType=extendedIfNoResult&enableGoogleStructuredDataAggregates=true&leadingCount=2"
    
    @staticmethod
    def build_pagination_url(base_url, start_index):
        """Update base URL with new start index for pagination"""
        return base_url.replace('"from":0', f'"from":{start_index}')
    
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