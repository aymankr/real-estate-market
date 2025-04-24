import logging

logger = logging.getLogger(__name__)

class PropertyDataExtractor:
    """Extract property data from BienIci responses"""
    
    @staticmethod
    def extract_insee_code(detail_data, basic_data, district_data):
        """
        Extract INSEE code from multiple potential sources, giving priority to direct INSEE code fields
        """
        # Try from district in details which is the most reliable source for INSEE code
        if 'district' in detail_data and isinstance(detail_data['district'], dict):
            district = detail_data['district']
            # First try with code_insee field
            if 'code_insee' in district:
                logger.debug(f"Found INSEE code in detail_data.district.code_insee: {district['code_insee']}")
                return district['code_insee']
            # Then try with insee_code field
            elif 'insee_code' in district:
                logger.debug(f"Found INSEE code in detail_data.district.insee_code: {district['insee_code']}")
                return district['insee_code']
        
        # Try from district metadata
        if district_data:
            if 'code_insee' in district_data:
                logger.debug(f"Found INSEE code in district_data.code_insee: {district_data['code_insee']}")
                return district_data['code_insee']
            elif 'insee_code' in district_data:
                logger.debug(f"Found INSEE code in district_data.insee_code: {district_data['insee_code']}")
                return district_data['insee_code']
        
        # If no INSEE code found, fall back to postal code
        postal_code = PropertyDataExtractor.extract_postal_code(detail_data, basic_data, district_data)
        logger.debug(f"No INSEE code found, using postal code as fallback: {postal_code}")
        return postal_code
    
    @staticmethod
    def extract_postal_code(detail_data, basic_data, district_data):
        """Extract postal code from multiple potential sources"""
        # Try from direct property
        if 'postalCode' in detail_data:
            return detail_data['postalCode']
        
        # Try from address
        if 'address' in detail_data and isinstance(detail_data['address'], dict):
            address = detail_data['address']
            if 'postalCode' in address:
                return address['postalCode']
        
        # Try from district in details
        if 'district' in detail_data and isinstance(detail_data['district'], dict):
            district = detail_data['district']
            if 'postal_code' in district:
                return district['postal_code']
            elif 'cp' in district:
                return district['cp']
        
        # Try from basic data
        if 'postalCode' in basic_data:
            return basic_data['postalCode']
        
        # Try from district in metadata
        if district_data:
            if 'postal_code' in district_data:
                return district_data['postal_code']
            elif 'cp' in district_data:
                return district_data['cp']
        
        # Default value
        return "00000"
    
    @staticmethod
    def extract_city(detail_data, basic_data):
        """Extract city name from available data"""
        if 'city' in detail_data:
            return detail_data['city']
        elif 'address' in detail_data and isinstance(detail_data['address'], dict) and 'city' in detail_data['address']:
            return detail_data['address']['city']
        elif 'city' in basic_data:
            return basic_data['city']
        return None
    
    @staticmethod
    def _extract_from_blur_info(data):
        """Extract coordinates from blur info if available"""
        if 'blurInfo' in data and isinstance(data['blurInfo'], dict) and 'position' in data['blurInfo']:
            blur_info = data['blurInfo']
            if 'position' in blur_info and 'lat' in blur_info['position'] and 'lon' in blur_info['position']:
                return blur_info['position']['lat'], blur_info['position']['lon']
        return None
    
    @staticmethod
    def extract_coordinates(detail_data, basic_data, city_insee_code):
        """Extract coordinates from multiple potential sources"""
        # Try from blurInfo.position in detail data
        coords = PropertyDataExtractor._extract_from_blur_info(detail_data)
        if coords:
            return coords
        
        # Try from coordinates in detail data
        if 'coordinates' in detail_data:
            if isinstance(detail_data['coordinates'], dict) and 'lat' in detail_data['coordinates'] and 'lng' in detail_data['coordinates']:
                return detail_data['coordinates']['lat'], detail_data['coordinates']['lng']
        
        # Try from blurInfo.position in basic data
        coords = PropertyDataExtractor._extract_from_blur_info(basic_data)
        if coords:
            return coords
        
        # No coordinates found
        return None, None 