"""
Alert processing engine for disaster risk assessment
"""
import logging
from datetime import datetime, timedelta
from database import get_latest_weather_data, insert_alert, get_active_alerts
from config import (
    LIGHT_RAIN_THRESHOLD, MODERATE_RAIN_THRESHOLD, HEAVY_RAIN_THRESHOLD,
    VERY_HEAVY_RAIN_THRESHOLD, EXTREME_RAIN_THRESHOLD,
    COLD_WAVE_THRESHOLD, SEVERE_COLD_THRESHOLD, HEAT_WAVE_THRESHOLD, SEVERE_HEAT_THRESHOLD,
    STRONG_WIND_THRESHOLD, HIGH_WIND_THRESHOLD, VERY_HIGH_WIND_THRESHOLD,
    LANDSLIDE_RAIN_INTENSITY, FLASH_FLOOD_RAIN_1H, HUMIDITY_HIGH_THRESHOLD,
    HP_ENHANCED_LOCATIONS, LOCATION_RISK_PROFILES, HP_DISTRICTS
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AlertEngine:
    def __init__(self):
        self.alert_history = []
        self.enhanced_locations = {loc['name']: loc for loc in HP_ENHANCED_LOCATIONS}
        self.location_profiles = LOCATION_RISK_PROFILES
    
    def _get_location_coords(self, location_name):
        """Helper to get coordinates for a given location name"""
        for loc in HP_ENHANCED_LOCATIONS:
            if loc['name'] == location_name:
                return loc
        for loc in HP_DISTRICTS:
            if loc['name'] == location_name:
                return loc
        return None

    def assess_weather_risk(self, weather_data):
        """Advanced disaster risk assessment for Himachal Pradesh with location-specific intelligence"""
        risks = []
        
        for record in weather_data:
            district, timestamp, temp, rainfall, wind_speed, humidity, pressure, description, source = record
            
            # Check if this is an enhanced location with specific risk profiles
            location_info = self.enhanced_locations.get(district, None)
            if location_info:
                location_type = location_info.get('type', 'district')
                elevation = location_info.get('elevation', 0)
                specific_risks = location_info.get('risk_factors', [])
            else:
                location_type = 'district'
                elevation = 0
                specific_risks = []
            
            risk_factors = []
            risk_score = 0
            alert_level = "Normal"
            disaster_types = []
            
            # Rainfall-based disaster assessment
            if rainfall is not None:
                if rainfall >= EXTREME_RAIN_THRESHOLD:
                    risk_factors.append(f"Extreme Rainfall: {rainfall} mm/h")
                    risk_score += 10
                    disaster_types.append("Flash Flood")
                    disaster_types.append("Landslide")
                elif rainfall >= VERY_HEAVY_RAIN_THRESHOLD:
                    risk_factors.append(f"Very Heavy Rain: {rainfall} mm/h")
                    risk_score += 7
                    disaster_types.append("Flash Flood Risk")
                    disaster_types.append("Landslide Risk")
                elif rainfall >= HEAVY_RAIN_THRESHOLD:
                    risk_factors.append(f"Heavy Rain: {rainfall} mm/h")
                    risk_score += 5
                    disaster_types.append("Flood Risk")
                elif rainfall >= MODERATE_RAIN_THRESHOLD:
                    risk_factors.append(f"Moderate Rain: {rainfall} mm/h")
                    risk_score += 3
                    disaster_types.append("Monitor")
                elif rainfall >= LIGHT_RAIN_THRESHOLD:
                    risk_factors.append(f"Light Rain: {rainfall} mm/h")
                    risk_score += 1
            
            # Temperature-based assessments
            if temp is not None:
                if temp <= SEVERE_COLD_THRESHOLD:
                    risk_factors.append(f"Severe Cold Wave: {temp}°C")
                    risk_score += 6
                    disaster_types.append("Severe Cold Wave")
                elif temp <= COLD_WAVE_THRESHOLD:
                    risk_factors.append(f"Cold Wave: {temp}°C")
                    risk_score += 4
                    disaster_types.append("Cold Wave")
                elif temp >= SEVERE_HEAT_THRESHOLD:
                    risk_factors.append(f"Severe Heat Wave: {temp}°C")
                    risk_score += 6
                    disaster_types.append("Heat Wave")
                elif temp >= HEAT_WAVE_THRESHOLD:
                    risk_factors.append(f"Heat Wave: {temp}°C")
                    risk_score += 4
                    disaster_types.append("Heat Wave")
            
            # Wind-based assessments
            if wind_speed is not None:
                if wind_speed >= VERY_HIGH_WIND_THRESHOLD:
                    risk_factors.append(f"Very High Winds: {wind_speed} m/s")
                    risk_score += 5
                    disaster_types.append("Storm Warning")
                elif wind_speed >= HIGH_WIND_THRESHOLD:
                    risk_factors.append(f"High Winds: {wind_speed} m/s")
                    risk_score += 3
                    disaster_types.append("Wind Alert")
                elif wind_speed >= STRONG_WIND_THRESHOLD:
                    risk_factors.append(f"Strong Winds: {wind_speed} m/s")
                    risk_score += 2
            
            # Enhanced location-specific risk assessment
            location_risk_bonus = self._assess_location_specific_risks(
                district, location_type, elevation, specific_risks, 
                temp, rainfall, wind_speed, humidity
            )
            risk_score += location_risk_bonus['risk_points']
            disaster_types.extend(location_risk_bonus['disaster_types'])
            risk_factors.extend(location_risk_bonus['risk_factors'])
            
            # Landslide risk assessment (enhanced with location intelligence)
            if rainfall is not None and humidity is not None:
                landslide_risk = self._assess_enhanced_landslide_risk(
                    district, location_type, elevation, rainfall, humidity, temp
                )
                if landslide_risk['risk_points'] > 0:
                    risk_score += landslide_risk['risk_points']
                    disaster_types.extend(landslide_risk['disaster_types'])
                    risk_factors.extend(landslide_risk['risk_factors'])
            
            # Flash flood assessment
            if rainfall is not None and rainfall >= FLASH_FLOOD_RAIN_1H:
                risk_factors.append(f"Flash Flood Conditions: {rainfall} mm/h")
                risk_score += 6
                disaster_types.append("Flash Flood Warning")
            
            # Composite risk conditions
            if humidity is not None and humidity >= HUMIDITY_HIGH_THRESHOLD and rainfall is not None and rainfall > 5:
                risk_factors.append(f"High Humidity + Rain: Landslide conditions")
                risk_score += 3
                disaster_types.append("Landslide Watch")
            
            # Determine alert level
            if risk_score >= 15:
                alert_level = "Emergency"
            elif risk_score >= 10:
                alert_level = "Critical"
            elif risk_score >= 6:
                alert_level = "High"
            elif risk_score >= 3:
                alert_level = "Moderate"
            elif risk_score >= 1:
                alert_level = "Low"
            
            risk_assessment = {
                'district': district,
                'timestamp': timestamp,
                'temperature': temp,
                'rainfall': rainfall,
                'wind_speed': wind_speed,
                'humidity': humidity,
                'pressure': pressure,
                'description': description,
                'risk_factors': risk_factors,
                'risk_score': risk_score,
                'alert_level': alert_level,
                'disaster_types': disaster_types,
                'landslide_risk': self._get_landslide_risk_category(district, rainfall, humidity) if rainfall else "Low"
            }
            
            risks.append(risk_assessment)
        
        return risks
    
    def _assess_location_specific_risks(self, location_name, location_type, elevation, specific_risks, temp, rainfall, wind_speed, humidity):
        """Assess risks specific to location type and characteristics"""
        result = {
            'risk_points': 0,
            'disaster_types': [],
            'risk_factors': []
        }
        
        # Get base risk profile for location type
        profile = self.location_profiles.get(location_type, {'base_risk': 0})
        base_risk = profile.get('base_risk', 0)
        result['risk_points'] += base_risk
        
        # Elevation-based risks
        if elevation > 3000:
            if temp is not None and temp < 0:
                result['risk_points'] += 3
                result['disaster_types'].append("Extreme Cold Risk")
                result['risk_factors'].append(f"High altitude + sub-zero temp: {elevation}m, {temp}°C")
            
            if wind_speed is not None and wind_speed > 10:
                result['risk_points'] += 2
                result['disaster_types'].append("High Altitude Wind Risk")
                result['risk_factors'].append(f"High altitude winds: {wind_speed} m/s at {elevation}m")
        
        elif elevation > 2000:
            if "landslide" in specific_risks and rainfall is not None and rainfall > 5:
                result['risk_points'] += 3
                result['disaster_types'].append("Hill Station Landslide Risk")
                result['risk_factors'].append(f"Hill station + rain: {elevation}m elevation")
        
        # River and water body specific risks
        if location_type in ['river', 'river_basin', 'valley']:
            if rainfall is not None and rainfall > 10:
                result['risk_points'] += 4
                result['disaster_types'].append("River Flash Flood Risk")
                result['risk_factors'].append(f"River area + heavy rain: {rainfall} mm/h")
            
            if rainfall is not None and rainfall > 5:
                result['risk_points'] += 2
                result['disaster_types'].append("Downstream Flood Risk")
                result['risk_factors'].append("Potential upstream water accumulation")
        
        # Dam zone specific risks
        if location_type == 'dam_zone':
            if rainfall is not None and rainfall > 15:
                result['risk_points'] += 5
                result['disaster_types'].append("Dam Safety Alert")
                result['risk_factors'].append(f"Heavy rain near dam infrastructure: {rainfall} mm/h")
        
        # Highway and pass specific risks
        if location_type in ['highway', 'mountain_pass', 'tunnel_zone']:
            if "landslide" in specific_risks and (rainfall is not None and rainfall > 3):
                result['risk_points'] += 4
                result['disaster_types'].append("Highway Landslide Risk")
                result['risk_factors'].append(f"Critical infrastructure + rain: {location_name}")
            
            if temp is not None and temp < 2:
                result['risk_points'] += 2
                result['disaster_types'].append("Road Ice Formation Risk")
                result['risk_factors'].append(f"Freezing conditions on roads: {temp}°C")
        
        # Tourism and populated areas
        if location_type in ['city', 'hill_station', 'town']:
            if base_risk > 0:
                result['risk_factors'].append(f"Populated area risk factor: {location_type}")
        
        return result
    
    def _assess_enhanced_landslide_risk(self, location_name, location_type, elevation, rainfall, humidity, temperature):
        """Enhanced landslide risk assessment with location intelligence"""
        result = {
            'risk_points': 0,
            'disaster_types': [],
            'risk_factors': []
        }
        
        high_susceptibility_areas = [
            "Shimla City", "Manali", "Dharamshala", "Kinnaur Highway", 
            "Rohtang Pass", "Kufri Hills", "Narkanda Slopes", "Kalpa"
        ]
        
        moderate_susceptibility_areas = [
            "Kasauli", "Dalhousie", "Palampur Valley", "Karsog Valley"
        ]
        
        base_susceptibility = 0
        if location_name in high_susceptibility_areas:
            base_susceptibility = 3
        elif location_name in moderate_susceptibility_areas:
            base_susceptibility = 2
        elif elevation > 1500:
            base_susceptibility = 2
        elif elevation > 1000:
            base_susceptibility = 1
        
        rainfall_risk = 0
        if rainfall >= 20:
            rainfall_risk = 6
            result['disaster_types'].append("Critical Landslide Risk")
        elif rainfall >= 10:
            rainfall_risk = 4
            result['disaster_types'].append("High Landslide Risk")
        elif rainfall >= 5:
            rainfall_risk = 2
            result['disaster_types'].append("Moderate Landslide Risk")
        elif rainfall >= 2.5:
            rainfall_risk = 1
            
        humidity_risk = 0
        if humidity >= 90:
            humidity_risk = 2
            result['risk_factors'].append(f"Very high humidity: {humidity}% - soil saturation risk")
        elif humidity >= 85:
            humidity_risk = 1
        
        temp_risk = 0
        if temperature is not None:
            if 0 <= temperature <= 5:
                temp_risk = 1
                result['risk_factors'].append(f"Freeze-thaw zone: {temperature}°C")
        
        total_risk = base_susceptibility + rainfall_risk + humidity_risk + temp_risk
        
        if total_risk >= 8:
            result['disaster_types'] = ["Critical Landslide Warning"]
            result['risk_factors'].append(f"URGENT: Immediate evacuation recommended - {location_name}")
        elif total_risk >= 6:
            result['disaster_types'] = ["High Landslide Risk"]
            result['risk_factors'].append(f"HIGH RISK: Close monitoring required - {location_name}")
        elif total_risk >= 4:
            result['disaster_types'] = ["Moderate Landslide Risk"]  
            result['risk_factors'].append(f"MODERATE: Increased vigilance - {location_name}")
        elif total_risk >= 2:
            result['disaster_types'] = ["Low Landslide Watch"]
            result['risk_factors'].append(f"Monitor conditions - {location_name}")
        
        result['risk_points'] = total_risk
        
        if total_risk > 0:
            result['risk_factors'].append(f"Landslide risk score: {total_risk}/12 for {location_name}")
        
        return result
    
    def _assess_landslide_risk(self, rainfall, humidity, temperature):
        """Calculate landslide risk based on multiple factors"""
        risk_score = 0
        
        # Rainfall intensity factor
        if rainfall >= LANDSLIDE_RAIN_INTENSITY:
            risk_score += 5
        elif rainfall >= 7.0:
            risk_score += 3
        elif rainfall >= 5.0:
            risk_score += 2
        
        # Humidity factor
        if humidity >= 90:
            risk_score += 3
        elif humidity >= 85:
            risk_score += 2
        
        # Temperature factor (wet conditions in moderate temps increase risk)
        if temperature is not None and 15 <= temperature <= 30:
            risk_score += 1
        
        return risk_score
    
    def _get_landslide_risk_category(self, district, rainfall, humidity):
        """Get landslide risk category for specific district"""
        # High-risk districts in HP
        high_risk_districts = ["Shimla", "Mandi", "Kullu", "Chamba", "Kinnaur"]
        
        if district in high_risk_districts:
            base_risk = 2
        else:
            base_risk = 1
        
        if rainfall is not None and rainfall > 10 and humidity > 85:
            return "Very High"
        elif rainfall is not None and rainfall > 7:
            return "High"
        elif rainfall is not None and rainfall > 3:
            return "Moderate"
        else:
            return "Low"
    
    def generate_alerts(self, risk_assessments):
        """
        Generate alerts based on advanced risk assessments.
        Returns a list of alert dictionaries, enriched with location coordinates.
        """
        new_alerts = []
        
        for risk in risk_assessments:
            if risk['risk_score'] >= 1:
                alert_type = self._determine_alert_type(risk['disaster_types'], risk['risk_factors'])
                message = self._create_alert_message(risk)
                
                # Get coordinates for the location
                location_coords = self._get_location_coords(risk['district'])
                
                alert = {
                    'district': risk['district'],
                    'alert_type': alert_type,
                    'severity': risk['alert_level'],
                    'message': message,
                    'timestamp': datetime.now(),
                    'risk_data': risk,
                    'disaster_types': risk['disaster_types'],
                    'landslide_risk': risk.get('landslide_risk', 'Low'),
                    'latitude': location_coords['lat'] if location_coords else None,
                    'longitude': location_coords['lon'] if location_coords else None
                }
                
                new_alerts.append(alert)
                
                # Store alert in database
                insert_alert(
                    risk['district'],
                    alert_type,
                    risk['alert_level'],
                    message
                )
                
                logger.info(f"ALERT: {risk['district']} - {alert_type} [{risk['alert_level']}] - Score: {risk['risk_score']}")
                logger.info(f"Disasters: {', '.join(risk['disaster_types'])}")
        
        return new_alerts
    
    def _determine_alert_type(self, disaster_types, risk_factors):
        """Determine alert type based on disaster types and risk factors"""
        if not disaster_types:
            return "Weather Advisory"
        
        if "Flash Flood" in disaster_types:
            return "Flash Flood Emergency"
        elif "Landslide" in disaster_types:
            return "Landslide Emergency"
        elif "Flash Flood Risk" in disaster_types or "Landslide Risk" in disaster_types:
            return "Flood/Landslide Warning"
        elif "High Landslide Risk" in disaster_types:
            return "Landslide Warning"
        elif "Severe Cold Wave" in disaster_types:
            return "Severe Cold Wave Alert"
        elif "Cold Wave" in disaster_types:
            return "Cold Wave Warning"
        elif "Heat Wave" in disaster_types:
            return "Heat Wave Warning"
        elif "Storm Warning" in disaster_types:
            return "Storm Warning"
        elif "Flash Flood Warning" in disaster_types:
            return "Flash Flood Warning"
        elif "Wind Alert" in disaster_types:
            return "High Wind Alert"
        elif "Flood Risk" in disaster_types:
            return "Flood Risk Advisory"
        elif "Landslide Watch" in disaster_types:
            return "Landslide Watch"
        elif "Monitor" in disaster_types:
            return "Weather Monitor"
        else:
            return f"{disaster_types[0]} Alert"
    
    def _create_alert_message(self, risk):
        """Create detailed alert message with disaster-specific guidance"""
        district = risk['district']
        risk_factors = risk['risk_factors']
        alert_level = risk['alert_level']
        disaster_types = risk.get('disaster_types', [])
        landslide_risk = risk.get('landslide_risk', 'Low')
        
        severity_emoji = {
            'Emergency': '🆘',
            'Critical': '🚨',
            'High': '⚠️',
            'Moderate': '⚡',
            'Low': '🌤️',
            'Normal': '✅'
        }
        
        message = f"{severity_emoji.get(alert_level, '⚠️')} {alert_level.upper()} ALERT - {district} District\n\n"
        
        if disaster_types:
            message += f"🎯 THREAT TYPE: {', '.join(disaster_types)}\n"
            message += f"🏔️ Landslide Risk: {landslide_risk}\n\n"
        
        message += "📊 CURRENT CONDITIONS:\n"
        message += f"🌡️ Temperature: {risk['temperature']}°C\n"
        message += f"🌧️ Rainfall: {risk['rainfall']} mm/h\n"
        message += f"💨 Wind Speed: {risk['wind_speed']} m/s\n"
        message += f"💧 Humidity: {risk['humidity']}%\n\n"
        
        if risk_factors:
            message += "⚡ RISK FACTORS:\n"
            for factor in risk_factors:
                message += f"• {factor}\n"
            message += "\n"
        
        message += "🆘 IMMEDIATE ACTIONS:\n"
        
        if any("Flash Flood" in dt for dt in disaster_types):
            message += "• MOVE TO HIGHER GROUND immediately\n"
            message += "• Avoid crossing flowing water\n"
            message += "• Stay away from rivers and streams\n"
        
        if any("Landslide" in dt for dt in disaster_types):
            message += "• EVACUATE steep slope areas now\n"
            message += "• Listen for rumbling sounds\n"
            message += "• Report cracks in ground/buildings\n"
        
        if any("Cold Wave" in dt for dt in disaster_types):
            message += "• Stay indoors and keep warm\n"
            message += "• Check on elderly neighbors\n"
            message += "• Protect livestock and water pipes\n"
        
        if any("Heat Wave" in dt for dt in disaster_types):
            message += "• Stay hydrated and avoid sun\n"
            message += "• Use cooling measures\n"
            message += "• Check on vulnerable people\n"
        
        if any("Storm" in dt or "Wind" in dt for dt in disaster_types):
            message += "• Secure loose objects outdoors\n"
            message += "• Stay away from trees and power lines\n"
            message += "• Avoid travel if possible\n"
        
        message += "• Keep emergency kit ready\n"
        message += "• Monitor official updates\n"
        message += "• Report emergencies to authorities\n\n"
        
        message += f"📅 Alert Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        message += f"📍 Risk Score: {risk['risk_score']}/20"
        
        return message
    
    def process_current_conditions(self):
        """Process current weather conditions and generate alerts if needed"""
        logger.info("Processing current weather conditions...")
        
        weather_data = get_latest_weather_data()
        
        if not weather_data:
            logger.warning("No weather data available for processing")
            return [], []
        
        risk_assessments = self.assess_weather_risk(weather_data)
        alerts = self.generate_alerts(risk_assessments)
        
        total_districts = len(risk_assessments)
        alert_districts = len(alerts)
        
        logger.info(f"Processed {total_districts} districts, generated {alert_districts} alerts")
        
        if alerts:
            logger.info("Districts with alerts:")
            for alert in alerts:
                logger.info(f"  {alert['district']}: {alert['alert_type']} - {alert['severity']}")
        
        return risk_assessments, alerts
    
    def get_current_status(self):
        """Get current system status and active alerts"""
        active_alerts = get_active_alerts()
        weather_data = get_latest_weather_data()
        
        status = {
            'total_districts': len(weather_data) if weather_data else 0,
            'active_alerts': len(active_alerts),
            'last_update': datetime.now(),
            'alerts': active_alerts,
            'weather_summary': []
        }
        
        if weather_data:
            for record in weather_data:
                district, timestamp, temp, rainfall, wind_speed, humidity, pressure, description, source = record
                status['weather_summary'].append({
                    'district': district,
                    'temperature': temp,
                    'rainfall': rainfall,
                    'wind_speed': wind_speed,
                    'description': description,
                    'last_update': timestamp
                })
        
        return status

def test_alert_engine():
    """Test the alert engine functionality"""
    engine = AlertEngine()
    
    print("=== Alert Engine Test ===")
    risk_assessments, alerts = engine.process_current_conditions()
    
    print(f"\nProcessed {len(risk_assessments)} districts")
    print(f"Generated {len(alerts)} alerts")
    
    if alerts:
        print("\n=== Generated Alerts ===")
        for alert in alerts:
            print(f"District: {alert['district']}")
            print(f"Type: {alert['alert_type']}")
            print(f"Severity: {alert['severity']}")
            print("---")
    else:
        print("\n✅ No alerts generated - All conditions normal")
    
    status = engine.get_current_status()
    print(f"\n=== System Status ===")
    print(f"Monitoring: {status['total_districts']} districts")
    print(f"Active Alerts: {status['active_alerts']}")
    print(f"Last Update: {status['last_update']}")

if __name__ == "__main__":
    test_alert_engine()