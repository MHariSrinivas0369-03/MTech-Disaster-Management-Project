"""
Enhanced data fetcher using Open-Meteo API for better precipitation data and disaster prediction
"""
import requests
import logging
import time
from datetime import datetime, timedelta
from database import insert_weather_data, insert_precipitation_accumulation
from config import HP_DISTRICTS, HP_ENHANCED_LOCATIONS

logger = logging.getLogger(__name__)

class DataFetcher:
    def __init__(self):
        # Open-Meteo API - no API key required, better precipitation data
        self.base_url = "https://api.open-meteo.com/v1/forecast"
        self.historical_url = "https://archive-api.open-meteo.com/v1/archive"
        
    def fetch_weather_for_location(self, location):
        """Fetch enhanced weather data with precipitation accumulations using Open-Meteo API"""
        try:
            # Get current and recent weather data from Open-Meteo
            params = {
                'latitude': location['lat'],
                'longitude': location['lon'],
                'current': 'temperature_2m,precipitation,wind_speed_10m,relative_humidity_2m,surface_pressure,weather_code',
                'hourly': 'temperature_2m,precipitation,wind_speed_10m,relative_humidity_2m',
                'past_days': 1,  # Get last 24 hours for accumulation
                'forecast_days': 1,
                'timezone': 'Asia/Kolkata'
            }
            
            response = requests.get(self.base_url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract current weather
            current = data['current']
            weather_code = current.get('weather_code', 0)
            description = self.get_weather_description(weather_code)
            
            # Extract hourly data for accumulations
            hourly = data['hourly']
            times = hourly['time']
            precipitation = hourly['precipitation']
            
            # Calculate rainfall accumulations
            current_time = datetime.now()
            rainfall_1h = current.get('precipitation', 0)
            rainfall_3h = sum(precipitation[-3:]) if len(precipitation) >= 3 else sum(precipitation)
            rainfall_24h = sum(precipitation[-24:]) if len(precipitation) >= 24 else sum(precipitation)
            
            # Calculate Antecedent Precipitation Index (API) - simplified version
            # API considers recent rainfall with exponential decay
            api = self.calculate_antecedent_precipitation_index(precipitation)
            
            weather_info = {
                'location': location['name'],
                'district': location.get('district', location['name']),
                'temperature': current['temperature_2m'],
                'rainfall': rainfall_1h,
                'wind_speed': current['wind_speed_10m'],
                'humidity': current['relative_humidity_2m'],
                'pressure': current['surface_pressure'],
                'description': description,
                'timestamp': current_time,
                'rainfall_3h': rainfall_3h,
                'rainfall_24h': rainfall_24h,
                'api': api
            }
            
            # Store basic weather data
            insert_weather_data(
                district=weather_info['district'],
                temperature=weather_info['temperature'],
                rainfall=weather_info['rainfall'],
                wind_speed=weather_info['wind_speed'],
                humidity=weather_info['humidity'],
                pressure=weather_info['pressure'],
                description=weather_info['description'],
                source='Open-Meteo'
            )
            
            # Store precipitation accumulation data for disaster prediction
            insert_precipitation_accumulation(
                district=weather_info['district'],
                rainfall_1h=rainfall_1h,
                rainfall_3h=rainfall_3h,
                rainfall_24h=rainfall_24h,
                api=api,
                source='Open-Meteo'
            )
            
            logger.info(f"Weather data collected for {location['name']}")
            return weather_info
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching weather for {location['name']}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error for {location['name']}: {str(e)}")
            return None
    
    def get_weather_description(self, weather_code):
        """Convert Open-Meteo weather code to description"""
        weather_codes = {
            0: "Clear sky",
            1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
            45: "Fog", 48: "Depositing rime fog",
            51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
            56: "Light freezing drizzle", 57: "Dense freezing drizzle",
            61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
            66: "Light freezing rain", 67: "Heavy freezing rain",
            71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
            77: "Snow grains",
            80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
            85: "Slight snow showers", 86: "Heavy snow showers",
            95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail"
        }
        return weather_codes.get(weather_code, "Unknown")
    
    def calculate_antecedent_precipitation_index(self, precipitation_data):
        """Calculate Antecedent Precipitation Index for landslide risk assessment"""
        if not precipitation_data:
            return 0.0
        
        # Simplified API calculation - exponential decay of recent rainfall
        api = 0.0
        decay_factor = 0.9  # Daily decay rate
        
        for i, precip in enumerate(reversed(precipitation_data[-24:])):  # Last 24 hours
            hours_ago = i + 1
            decay = decay_factor ** (hours_ago / 24.0)  # Decay over days
            api += precip * decay
        
        return api
    
    def collect_all_data(self):
        """Collect weather data for all configured locations"""
        logger.info("Starting weather data collection cycle...")
        
        all_locations = HP_DISTRICTS + HP_ENHANCED_LOCATIONS
        successful_collections = 0
        weather_data = []
        
        for location in all_locations:
            weather_info = self.fetch_weather_for_location(location)
            if weather_info:
                weather_data.append(weather_info)
                successful_collections += 1
            
            # Small delay to respect API rate limits
            time.sleep(0.1)
        
        logger.info(f"Weather data collection completed: {successful_collections}/{len(all_locations)} successful")
        return weather_data
    
    def get_latest_weather_summary(self):
        """Get a summary of the latest weather conditions"""
        from database import get_latest_weather_data
        
        weather_data = get_latest_weather_data()
        if not weather_data:
            return None
        
        # Convert to list of dictionaries for easier processing
        weather_list = []
        for row in weather_data:
            weather_dict = {
                'district': row[0],
                'timestamp': row[1],
                'temperature': row[2],
                'rainfall': row[3],
                'wind_speed': row[4],
                'humidity': row[5],
                'pressure': row[6],
                'description': row[7],
                'source': row[8]
            }
            weather_list.append(weather_dict)
        
        return weather_list
