"""
Configuration settings for the Himachal Pradesh Disaster Alert System
"""
import os

# Database configuration
DATABASE_PATH = 'disaster_alert.db'

# API Configuration
OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY", "8c8a4d17fd1c2424c3459856d2c401c8")

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8478535363:AAFOBDMHyLzINxE9SEElZdBRJJGva3OlW9g")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "1858574343")

# System Configuration
DATA_COLLECTION_INTERVAL = 2  # minutes between data collection cycles
NUMBER_OF_VOLUNTEERS = 50  # number of volunteers to generate

# Alert sensitivity for demo purposes (now deterministic)
DEMO_MODE = True  # Set to True for enhanced alert generation during demos
ALERT_SENSITIVITY_MULTIPLIER = 1.3  # Deterministic sensitivity increase for demo

# Himachal Pradesh Districts with coordinates
HP_DISTRICTS = [
    {"name": "Shimla", "lat": 31.1048, "lon": 77.1734, "district": "Shimla"},
    {"name": "Manali", "lat": 32.2396, "lon": 77.1887, "district": "Kullu"},
    {"name": "Dharamshala", "lat": 32.2190, "lon": 76.3234, "district": "Kangra"},
    {"name": "Kullu", "lat": 31.9576, "lon": 77.1091, "district": "Kullu"},
    {"name": "Chamba", "lat": 32.5564, "lon": 76.1318, "district": "Chamba"},
    {"name": "Mandi", "lat": 31.7085, "lon": 76.9319, "district": "Mandi"},
    {"name": "Bilaspur", "lat": 31.3304, "lon": 76.7570, "district": "Bilaspur"},
    {"name": "Hamirpur", "lat": 31.6839, "lon": 76.5226, "district": "Hamirpur"},
    {"name": "Una", "lat": 31.4648, "lon": 76.2673, "district": "Una"},
    {"name": "Kangra", "lat": 32.0998, "lon": 76.2691, "district": "Kangra"},
    {"name": "Lahaul and Spiti", "lat": 32.7731, "lon": 77.0380, "district": "Lahaul and Spiti"},
    {"name": "Kinnaur", "lat": 31.6046, "lon": 78.3887, "district": "Kinnaur"},
    {"name": "Sirmaur", "lat": 30.5286, "lon": 77.3104, "district": "Sirmaur"},
    {"name": "Solan", "lat": 30.9045, "lon": 77.0967, "district": "Solan"}
]

# Enhanced locations for better coverage
HP_ENHANCED_LOCATIONS = [
    {"name": "Kasauli", "lat": 30.8978, "lon": 76.9657, "district": "Solan"},
    {"name": "Dalhousie", "lat": 32.5448, "lon": 75.9618, "district": "Chamba"},
    {"name": "Palampur", "lat": 32.1085, "lon": 76.5318, "district": "Kangra"},
    {"name": "Nalagarh", "lat": 30.9295, "lon": 76.6981, "district": "Solan"},
    {"name": "Paonta Sahib", "lat": 30.4401, "lon": 77.6183, "district": "Sirmaur"},
    {"name": "Sundarnagar", "lat": 31.5304, "lon": 76.8951, "district": "Mandi"},
    {"name": "Jogindernagar", "lat": 32.0599, "lon": 76.7959, "district": "Mandi"},
    {"name": "Baijnath", "lat": 32.0520, "lon": 76.6468, "district": "Kangra"},
    {"name": "Nurpur", "lat": 32.2951, "lon": 75.9004, "district": "Kangra"},
    {"name": "Dehra", "lat": 32.2032, "lon": 76.0839, "district": "Kangra"},
    {"name": "Arki", "lat": 31.1521, "lon": 76.9658, "district": "Solan"},
    {"name": "Theog", "lat": 31.1197, "lon": 77.3464, "district": "Shimla"},
    {"name": "Rohru", "lat": 31.2070, "lon": 77.7513, "district": "Shimla"},
    {"name": "Jubbal", "lat": 31.1095, "lon": 77.6523, "district": "Shimla"},
    {"name": "Kotkhai", "lat": 31.2928, "lon": 77.5773, "district": "Shimla"},
    {"name": "Ghumarwin", "lat": 31.4408, "lon": 76.7093, "district": "Bilaspur"},
    {"name": "Sarkaghat", "lat": 31.7014, "lon": 76.7318, "district": "Mandi"},
    {"name": "Nagrota Bagwan", "lat": 32.0963, "lon": 76.0869, "district": "Kangra"},
    {"name": "Parwanoo", "lat": 30.8439, "lon": 76.9719, "district": "Solan"},
    {"name": "Baddi", "lat": 30.9579, "lon": 76.7913, "district": "Solan"}
]

# Volunteer data for generation
VOLUNTEER_NAME_PREFIXES = [
    "Rahul", "Priya", "Amit", "Sunita", "Vikash", "Meera", "Rajesh", "Kavita",
    "Suresh", "Anita", "Manoj", "Deepika", "Ravi", "Pooja", "Sanjay", "Neha",
    "Arun", "Geeta", "Vinod", "Seema", "Ashok", "Reena", "Ramesh", "Shanti",
    "Mohan", "Usha", "Dinesh", "Sushma", "Kishore", "Nisha", "Prakash", "Vandana"
]

VOLUNTEER_SKILLS = [
    "First Aid", "Search and Rescue", "Medical Assistance", "Emergency Communication",
    "Evacuation Support", "Relief Distribution", "Technical Rescue", "Community Coordination",
    "Transportation", "Shelter Management", "Food Distribution", "Water Purification"
]

# Alert thresholds (adjusted for demo purposes)
ALERT_THRESHOLDS = {
    "rainfall": {
        "moderate": 15.0,  # mm/hour - lowered for demo
        "high": 25.0,      # mm/hour 
        "critical": 40.0   # mm/hour
    },
    "temperature": {
        "heat_moderate": 35.0,  # °C
        "heat_high": 40.0,      # °C
        "cold_moderate": 0.0,   # °C
        "cold_high": -5.0       # °C
    },
    "wind_speed": {
        "moderate": 25.0,  # km/h - lowered for demo
        "high": 40.0,      # km/h
        "critical": 60.0   # km/h
    },
    "humidity": {
        "low": 30.0,       # % - for fire risk
        "high": 85.0       # % - for flood/landslide risk
    }
}

# ML model predictions weight in final alert decision
ML_PREDICTION_WEIGHT = 0.0  # Temporarily disabled - ML predictions need retraining with real features
