"""
Configuration settings for the Himachal Pradesh Disaster Alert System
"""
import os
import random

# API Configuration
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "8c8a4d17fd1c2424c3459856d2c401c8")
NASA_USERNAME = os.getenv("NASA_USERNAME", "harisrinivas03")
NASA_PASSWORD = os.getenv("NASA_PASSWORD", "Saritha@2003")
NASA_EARTHDATA_TOKEN = os.getenv("NASA_EARTHDATA_TOKEN", "eyJ0eXAiOiJKV1QiLCJvcmlnaW4iOiJFYXJ0aGRhdGEgTG9naW4iLCJzaWciOiJlZGxqd3RwdWJrZXlfb3BzIiwiYWxnIjoiUlMyNTYifQ.eyJ0eXAiOiJKV1QiLCJvcmlnaW4iOiJFYXJ0aGRhdGEgTG9naW4iLCJzaWciOiJlZGxqd3RwdWJrZXlfb3BzIiwiYWxnIjoiUlMyNTYifQ.eyJ0eXBlIjoiVXNlciIsInVpZCI6ImhhcmlzcmluaXZhczAzIiwiZXhwIjoxNzYwNzQ1NTk5LCJpYXQiOjE3NTU1NjE1OTksImlzcyI6Imh0dHBzOi8vdXJzLmVhcnRoZGF0YS5uYXNhLmdvdiJ9")

# Climate Data Store Configuration
CDS_URL = os.getenv("CDS_URL", "https://cds.climate.copernicus.eu/api")
CDS_API_KEY = os.getenv("CDS_API_KEY", "d1419e08-858a-4adb-b23d-1d2e3e3a7048")

# Alert Thresholds (Based on IMD and HP disaster patterns)
# Rainfall thresholds
LIGHT_RAIN_THRESHOLD = 2.5      # mm/hour - Start monitoring
MODERATE_RAIN_THRESHOLD = 7.5   # mm/hour - Moderate alert
HEAVY_RAIN_THRESHOLD = 15.0     # mm/hour - High alert
VERY_HEAVY_RAIN_THRESHOLD = 25.0 # mm/hour - Critical alert
EXTREME_RAIN_THRESHOLD = 50.0   # mm/hour - Emergency

# Temperature thresholds for HP
COLD_WAVE_THRESHOLD = 5.0       # °C - Cold wave in plains
SEVERE_COLD_THRESHOLD = 2.0     # °C - Severe cold
HEAT_WAVE_THRESHOLD = 35.0      # °C - Heat wave (adjusted for HP climate)
SEVERE_HEAT_THRESHOLD = 40.0    # °C - Severe heat wave

# Wind thresholds
STRONG_WIND_THRESHOLD = 5.0     # m/s - Strong winds
HIGH_WIND_THRESHOLD = 10.0      # m/s - High winds  
VERY_HIGH_WIND_THRESHOLD = 15.0 # m/s - Very high winds

# Landslide risk factors
LANDSLIDE_RAIN_24H_THRESHOLD = 100.0   # mm in 24 hours
LANDSLIDE_RAIN_48H_THRESHOLD = 150.0   # mm in 48 hours
LANDSLIDE_RAIN_INTENSITY = 10.0      # mm/hour sustained

# Flash flood indicators
FLASH_FLOOD_RAIN_1H = 20.0     # mm in 1 hour
FLASH_FLOOD_RAIN_3H = 50.0     # mm in 3 hours

# Composite risk scoring
HUMIDITY_HIGH_THRESHOLD = 85.0   # % - High humidity increases landslide risk
PRESSURE_DROP_THRESHOLD = 10.0   # hPa drop indicates storm approach

# Himachal Pradesh Districts
HP_DISTRICTS = [
    {"name": "Shimla", "lat": 31.1048, "lon": 77.1734},
    {"name": "Mandi", "lat": 31.7084, "lon": 76.9319},
    {"name": "Kullu", "lat": 31.9583, "lon": 77.1096},
    {"name": "Kangra", "lat": 32.0998, "lon": 76.2695},
    {"name": "Chamba", "lat": 32.5563, "lon": 76.1264},
    {"name": "Una", "lat": 31.4685, "lon": 76.2714},
    {"name": "Bilaspur", "lat": 31.3317, "lon": 76.7553},
    {"name": "Hamirpur", "lat": 31.6839, "lon": 76.5225},
    {"name": "Solan", "lat": 30.9045, "lon": 77.0967},
    {"name": "Sirmaur", "lat": 30.5726, "lon": 77.2879},
    {"name": "Kinnaur", "lat": 31.6050, "lon": 78.2357},
    {"name": "Lahaul and Spiti", "lat": 32.5665, "lon": 77.0281}
]

# Enhanced Location-Based Monitoring Points
# Major Cities, Hill Stations, River Areas, and Landslide-Prone Zones
HP_ENHANCED_LOCATIONS = [
    {"name": "Shimla City", "lat": 31.1048, "lon": 77.1734, "type": "city", "district": "Shimla", "elevation": 2200, "risk_factors": ["landslide", "avalanche"]},
    {"name": "Manali", "lat": 32.2396, "lon": 77.1887, "type": "city", "district": "Kullu", "elevation": 2050, "risk_factors": ["landslide", "flash_flood", "avalanche"]},
    {"name": "Dharamshala", "lat": 32.2190, "lon": 76.3234, "type": "city", "district": "Kangra", "elevation": 1475, "risk_factors": ["landslide", "flash_flood"]},
    {"name": "Kasauli", "lat": 30.8987, "lon": 76.9656, "type": "hill_station", "district": "Solan", "elevation": 1927, "risk_factors": ["landslide"]},
    {"name": "Dalhousie", "lat": 32.5444, "lon": 76.0174, "type": "hill_station", "district": "Chamba", "elevation": 2036, "risk_factors": ["landslide", "heavy_snow"]},
    {"name": "Kinnaur Highway", "lat": 31.5804, "lon": 78.4568, "type": "highway", "district": "Kinnaur", "elevation": 3500, "risk_factors": ["landslide", "rockfall", "avalanche"]},
    {"name": "Rohtang Pass", "lat": 32.3730, "lon": 77.2497, "type": "mountain_pass", "district": "Kullu", "elevation": 3978, "risk_factors": ["avalanche", "landslide", "heavy_snow"]},
    {"name": "Aut Tunnel Area", "lat": 31.8368, "lon": 77.1147, "type": "tunnel_zone", "district": "Kullu", "elevation": 1100, "risk_factors": ["landslide", "flash_flood"]},
    {"name": "Kufri Hills", "lat": 31.1156, "lon": 77.2610, "type": "hill_area", "district": "Shimla", "elevation": 2720, "risk_factors": ["landslide", "heavy_snow"]},
    {"name": "Narkanda Slopes", "lat": 31.2772, "lon": 77.3785, "type": "slope_area", "district": "Shimla", "elevation": 2708, "risk_factors": ["landslide", "avalanche"]},
    {"name": "Beas River - Kullu", "lat": 31.9583, "lon": 77.1096, "type": "river", "district": "Kullu", "elevation": 1200, "risk_factors": ["flash_flood", "river_flood"]},
    {"name": "Sutlej River - Bilaspur", "lat": 31.3317, "lon": 76.7553, "type": "river", "district": "Bilaspur", "elevation": 673, "risk_factors": ["flash_flood", "dam_overflow"]},
    {"name": "Ravi River - Chamba", "lat": 32.5563, "lon": 76.1264, "type": "river", "district": "Chamba", "elevation": 996, "risk_factors": ["flash_flood", "glacial_melt"]},
    {"name": "Yamuna River - Sirmaur", "lat": 30.5726, "lon": 77.2879, "type": "river", "district": "Sirmaur", "elevation": 932, "risk_factors": ["flash_flood", "monsoon_flood"]},
    {"name": "Chenab River Basin", "lat": 32.4500, "lon": 76.0500, "type": "river_basin", "district": "Chamba", "elevation": 1200, "risk_factors": ["flash_flood", "glacial_lake_burst"]},
    {"name": "Palampur Valley", "lat": 32.1104, "lon": 76.5365, "type": "valley", "district": "Kangra", "elevation": 1220, "risk_factors": ["flash_flood", "landslide"]},
    {"name": "Karsog Valley", "lat": 31.3833, "lon": 76.7833, "type": "valley", "district": "Mandi", "elevation": 1200, "risk_factors": ["flash_flood", "landslide"]},
    {"name": "Joginder Nagar", "lat": 31.9858, "lon": 76.7658, "type": "town", "district": "Mandi", "elevation": 1224, "risk_factors": ["flash_flood", "dam_related"]},
    {"name": "Keylong", "lat": 32.5734, "lon": 77.0240, "type": "high_altitude", "district": "Lahaul and Spiti", "elevation": 3350, "risk_factors": ["avalanche", "extreme_cold", "landslide"]},
    {"name": "Kaza", "lat": 32.2237, "lon": 78.0707, "type": "high_altitude", "district": "Lahaul and Spiti", "elevation": 3650, "risk_factors": ["avalanche", "extreme_cold", "flash_flood"]},
    {"name": "Kalpa", "lat": 31.5361, "lon": 78.2592, "type": "high_altitude", "district": "Kinnaur", "elevation": 2960, "risk_factors": ["avalanche", "landslide", "extreme_cold"]},
    {"name": "Bhakra Dam Area", "lat": 31.4086, "lon": 76.4348, "type": "dam_zone", "district": "Bilaspur", "elevation": 518, "risk_factors": ["dam_safety", "flash_flood"]},
    {"name": "Pong Dam Area", "lat": 32.0500, "lon": 76.0500, "type": "dam_zone", "district": "Kangra", "elevation": 435, "risk_factors": ["dam_safety", "flash_flood"]},
    {"name": "Pangi Valley", "lat": 32.8500, "lon": 76.3167, "type": "remote_valley", "district": "Chamba", "elevation": 2400, "risk_factors": ["landslide", "avalanche", "isolation"]},
    {"name": "Pin Valley", "lat": 32.2000, "lon": 78.0500, "type": "remote_valley", "district": "Lahaul and Spiti", "elevation": 3500, "risk_factors": ["avalanche", "extreme_cold", "flash_flood"]}
]

# Risk Classification by Location Type
LOCATION_RISK_PROFILES = {
    "city": {"base_risk": 2, "population_factor": 3},
    "hill_station": {"base_risk": 3, "elevation_factor": 2, "tourism_factor": 2},
    "highway": {"base_risk": 4, "traffic_factor": 3},
    "mountain_pass": {"base_risk": 5, "weather_sensitivity": 4},
    "river": {"base_risk": 4, "monsoon_factor": 3},
    "river_basin": {"base_risk": 4, "upstream_factor": 2},
    "valley": {"base_risk": 3, "drainage_factor": 3},
    "high_altitude": {"base_risk": 4, "extreme_weather_factor": 4},
    "dam_zone": {"base_risk": 5, "infrastructure_factor": 4},
    "remote_valley": {"base_risk": 3, "isolation_factor": 5}
}

# Database Configuration
DATABASE_PATH = "disaster_alert.db"

# Data Collection Interval (minutes)
DATA_COLLECTION_INTERVAL = 30

# Volunteer Generation Configuration
NUMBER_OF_VOLUNTEERS = 200
VOLUNTEER_NAME_PREFIXES = [
    "Volunteer", "Rescue", "Help", "Team", "Guardian"
]
VOLUNTEER_SKILLS = [
    "First Aid", "Search & Rescue", "Crowd Management", "Communications",
    "Medical Assistance", "Technical Skills (e.g., drone ops)", "Logistics",
    "Psychological First Aid", "Debris Removal", "Shelter Management"
]