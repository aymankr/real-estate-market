import urllib.parse
import requests
import logging
from .items import BuildingType

logger = logging.getLogger(__name__)

class LocationService:
    """Utility service for location-related operations"""
    
    @staticmethod
    def get_coordinates_from_place(city, postal_code):
        """Get geographical coordinates for a city from its name and postal code"""
        try:
            # Use URL builder if available
            try:
                from .spiders.url_builder import BienIciUrlBuilder
                url = BienIciUrlBuilder.build_geocoding_url(city, postal_code)
            except (ImportError, ModuleNotFoundError):
                # Fallback if URL builder not available
                query = f"{city}-{postal_code}"
                params = {
                    "q": query,
                    "type": "city,delegated-city,department,postalCode,region",
                    "prefix": "no"
                }
                base_url = "https://res.bienici.com/place.json"
                query_string = urllib.parse.urlencode(params)
                url = f"{base_url}?{query_string}"
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "application/json",
                "Referer": "https://www.bienici.com/"
            }
            
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list) and len(data) > 0:
                    result = data[0]
                    
                    if 'lat' in result and 'lon' in result:
                        return result['lat'], result['lon']
                    
                    boundingBox = result.get("boundingBox")
                    if boundingBox:
                        lat = (boundingBox.get("south", 0) + boundingBox.get("north", 0)) / 2.0
                        lon = (boundingBox.get("west", 0) + boundingBox.get("east", 0)) / 2.0
                        return lat, lon
                
                logger.warning(f"No geocoding data found for {city}-{postal_code}")
            else:
                logger.error(f"Geocoding error ({resp.status_code}) for {city}-{postal_code}")
                
        except Exception as e:
            logger.error(f"Exception during geocoding for {city}-{postal_code}: {str(e)}")
        
        return 0.0, 0.0


class BuildingTypeConverter:
    """
    Utility class for converting BienIci building types to BuildingType enum values
    as defined in the items.py module
    """
    
    # Mapping of BienIci building types to BuildingType enum values
    BUILDING_TYPE_MAPPING = {
        # Residential properties
        "house": BuildingType.HOUSE,
        "flat": BuildingType.APARTMENT,
        "apartment": BuildingType.APARTMENT,
        "loft": BuildingType.APARTMENT,
        "townhouse": BuildingType.HOUSE,
        "castle": BuildingType.HOUSE,
        
        # Land
        "terrain": BuildingType.LAND,
        "land": BuildingType.LAND,
        
        # Commercial properties
        "parking": BuildingType.PARKING,
        "office": BuildingType.OFFICE,
        "bureau": BuildingType.OFFICE,
        "commerce": BuildingType.SHOP,
        "shop": BuildingType.SHOP,
        "local_commercial": BuildingType.SHOP,
        "entrepot": BuildingType.WAREHOUSE,
        "warehouse": BuildingType.WAREHOUSE,
        
        # New construction
        "programme": BuildingType.BUILDING,
        "immeuble": BuildingType.BUILDING,
        "building": BuildingType.BUILDING,
        
        # Default
        "other": BuildingType.OTHER
    }
    
    @staticmethod
    def from_bienici_type(building_type):
        """
        Convert BienIci building type to BuildingType enum value
        
        Args:
            building_type (str): The building type from BienIci API
            
        Returns:
            BuildingType: BuildingType enum value
        """
        if not building_type:
            logger.warning("No building type provided, using default type OTHER")
            return BuildingType.OTHER
            
        # Convert to lowercase for case-insensitive matching
        normalized_type = building_type.lower()
        
        # Get the mapped value or OTHER if not found
        building_type_enum = BuildingTypeConverter.BUILDING_TYPE_MAPPING.get(
            normalized_type, 
            BuildingType.OTHER
        )
        
        # Log for debugging
        if building_type_enum == BuildingType.OTHER and normalized_type != "other":
            logger.warning(f"Unknown building type: '{building_type}', using default type OTHER")
        else:
            logger.debug(f"Converted building type '{building_type}' to building type enum: {building_type_enum}")
            
        return building_type_enum 