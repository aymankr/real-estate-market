import requests
import logging
from .items import BuildingType

logger = logging.getLogger(__name__)

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
            building_type (str): The building type from BienIci
            
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