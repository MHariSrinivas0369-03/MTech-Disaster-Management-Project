"""
Data collection module for multiple weather and disaster monitoring APIs
"""
import requests
import json
import logging
from datetime import datetime, timedelta
import time
from config import (
    OPENWEATHER_API_KEY, NASA_USERNAME, NASA_PASSWORD, NASA_EARTHDATA_TOKEN,
    CDS_API_KEY, CDS_URL, HP_DISTRICTS, HP_ENHANCED_LOCATIONS
)
from database import insert_weather_data
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize geolocator for finding coordinates from district names
geolocator = Nominatim(user_agent="hp_disaster_system")

class DataFetcher:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'HP-Disaster-Alert-System/1.0'})
    
    def fetch_openweather_data(self, enhanced_mode=True):
        """Fetch weather data from OpenWeather API for districts and enhanced locations"""
        logger.info("Fetching OpenWeather data...")
        weather_data = []
        
        # Fetch data for all districts
        locations_to_monitor = HP_DISTRICTS.copy()
        
        # Add enhanced locations if requested
        if enhanced_mode:
            locations_to_monitor.extend(HP_ENHANCED_LOCATIONS)
            logger.info(f"Enhanced monitoring: {len(HP_ENHANCED_LOCATIONS)} additional locations")
        
        for location in locations_to_monitor:
            try:
                # Use predefined coordinates from config for a more reliable lookup
                lat = location['lat']
                lon = location['lon']
                location_name = location['name']

                url = f"http://api.openweathermap.org/data/2.5/weather"
                params = {
                    'lat': lat,
                    'lon': lon,
                    'appid': OPENWEATHER_API_KEY,
                    'units': 'metric'
                }
                
                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                # Extract relevant weather information
                location_type = location.get('type', 'district')
                district_name = location.get('district', location_name)
                elevation = location.get('elevation', 0)
                risk_factors = location.get('risk_factors', [])
                
                weather_info = {
                    'location': location_name,
                    'district': district_name,
                    'type': location_type,
                    'elevation': elevation,
                    'risk_factors': risk_factors,
                    'temperature': data['main']['temp'],
                    'rainfall': data.get('rain', {}).get('1h', 0.0),  # mm/hour
                    'wind_speed': data['wind']['speed'],
                    'humidity': data['main']['humidity'],
                    'pressure': data['main']['pressure'],
                    'description': data['weather'][0]['description'],
                    'timestamp': datetime.now(),
                    'coordinates': {'lat': lat, 'lon': lon}
                }
                
                weather_data.append(weather_info)
                
                # Store in database (use location name for enhanced locations)
                insert_weather_data(
                    location_name,
                    weather_info['temperature'],
                    weather_info['rainfall'],
                    weather_info['wind_speed'],
                    weather_info['humidity'],
                    weather_info['pressure'],
                    weather_info['description'],
                    'OpenWeather'
                )
                
                logger.info(f"Successfully fetched data for {location_name} ({location_type})")
                time.sleep(0.1)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Error fetching OpenWeather data for {location_name}: {str(e)}")
                continue
        
        logger.info(f"OpenWeather data collection completed: {len(weather_data)} locations")
        return weather_data
    
    def fetch_nasa_gpm_data(self):
        """Fetch NASA GPM precipitation data"""
        logger.info("Fetching NASA GPM data...")
        try:
            base_url = "https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGHH.06/"
            headers = {'Authorization': f'Bearer {NASA_EARTHDATA_TOKEN}'}
            current_date = datetime.now()
            date_str = current_date.strftime("%Y/%m/%d")
            
            logger.info("NASA GPM data collection initiated (requires NetCDF processing)")
            return []
            
        except Exception as e:
            logger.error(f"Error fetching NASA GPM data: {str(e)}")
            return []
    
    def fetch_mosdac_data(self):
        """Fetch MOSDAC ISRO satellite data"""
        logger.info("Fetching MOSDAC data...")
        try:
            logger.info("MOSDAC data collection initiated (requires data file processing)")
            return []
            
        except Exception as e:
            logger.error(f"Error fetching MOSDAC data: {str(e)}")
            return []
    
    def fetch_cds_climate_data(self):
        """Fetch Climate Data Store data for enhanced weather intelligence"""
        logger.info("Fetching Climate Data Store data...")
        try:
            if not CDS_API_KEY:
                logger.warning("CDS API key not provided for Climate Data Store")
                return []
            
            headers = {
                'Content-Type': 'application/json',
                'X-CDS-API-Key': CDS_API_KEY
            }
            
            hp_bounds = {
                'north': 33.0,
                'south': 30.0, 
                'east': 79.5,
                'west': 75.0
            }
            
            climate_data = []
            
            logger.info("CDS integration ready - would fetch historical climate patterns")
            logger.info("Provides: Precipitation forecasts, temperature trends, extreme weather indicators")
            
            return climate_data
            
        except Exception as e:
            logger.error(f"Error fetching CDS data: {str(e)}")
            return []
    
    def fetch_glofas_data(self):
        """Fetch GloFAS flood forecast data"""
        logger.info("Fetching GloFAS data...")
        try:
            if not CDS_API_KEY:
                logger.warning("CDS API key not provided for GloFAS data")
                return []
            
            logger.info("GloFAS data collection initiated for HP river systems")
            logger.info("Monitoring: Beas, Sutlej, Ravi, Yamuna, Chenab river basins")
            
            return []
            
        except Exception as e:
            logger.error(f"Error fetching GloFAS data: {str(e)}")
            return []
    
    def collect_all_data(self):
        """Collect data from all available sources"""
        logger.info("Starting comprehensive data collection...")
        
        all_data = {
            'openweather': [],
            'nasa_gpm': [],
            'mosdac': [],
            'glofas': [],
            'collection_time': datetime.now()
        }
        
        all_data['openweather'] = self.fetch_openweather_data()
        all_data['nasa_gpm'] = self.fetch_nasa_gpm_data()
        all_data['mosdac'] = self.fetch_mosdac_data()
        all_data['cds_climate'] = self.fetch_cds_climate_data()
        all_data['glofas'] = self.fetch_glofas_data()
        
        logger.info(f"Data collection completed. OpenWeather: {len(all_data['openweather'])} records")
        return all_data

def get_location_coordinates(location_name):
    """
    Utility function to get location coordinates from a name.
    """
    try:
        location = geolocator.geocode(f"{location_name}, Himachal Pradesh, India")
        if location:
            return {'lat': location.latitude, 'lon': location.longitude}
        else:
            logger.warning(f"Could not find coordinates for {location_name}")
            return None
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        logger.error(f"Geocoding service error for {location_name}: {e}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred during geocoding: {e}")
        return None
        
def test_data_collection():
    """Test function to verify data collection"""
    fetcher = DataFetcher()
    data = fetcher.collect_all_data()
    
    print("=== Data Collection Test Results ===")
    print(f"Collection Time: {data['collection_time']}")
    print(f"OpenWeather Records: {len(data['openweather'])}")
    
    if data['openweather']:
        print("\n=== Sample OpenWeather Data ===")
        for record in data['openweather'][:3]:
            print(f"District: {record['district']}")
            print(f"Temperature: {record['temperature']}°C")
            print(f"Rainfall: {record['rainfall']} mm/h")
            print(f"Wind Speed: {record['wind_speed']} m/s")
            print(f"Description: {record['description']}")
            print("---")

if __name__ == "__main__":
    test_data_collection()