"""
Enhanced Alert Engine with ML integration and NetCDF climatology for disaster prediction
"""
import logging
import json
from datetime import datetime
from database import insert_alert, get_latest_weather_data, get_precipitation_accumulations, get_rainfall_climatology
from ml_model import get_ml_predictions
from config import ALERT_THRESHOLDS, DEMO_MODE, ALERT_SENSITIVITY_MULTIPLIER, ML_PREDICTION_WEIGHT
import random

logger = logging.getLogger(__name__)

class AlertEngine:
    def __init__(self):
        self.current_alerts = []
        self.risk_assessments = {}
        
    def calculate_rainfall_risk(self, rainfall_mm, district_name=None, rainfall_1h=None, rainfall_24h=None, ml_prediction=0.0):
        """Calculate rainfall-based risk with NetCDF climatology enhancement and ML integration"""
        base_risk = 0.0
        alert_type = None
        severity = "Low"
        
        # Use provided values or fallback to basic rainfall
        rain_1h = rainfall_1h if rainfall_1h is not None else rainfall_mm
        rain_24h = rainfall_24h if rainfall_24h is not None else rainfall_mm * 24
        
        # Get district-specific climatology if available
        climatology_data = None
        rain_1h_anomaly = 1.0  # Default anomaly multiplier
        rain_24h_anomaly = 1.0
        
        # Initialize climatology percentiles with defaults
        p50_1h = p80_1h = p90_1h = p95_1h = p99_1h = 15.0  # Default 1h thresholds
        p50_24h = p80_24h = p90_24h = p95_24h = p99_24h = 360.0  # Default 24h thresholds
        
        if district_name:
            try:
                climatology_data = get_rainfall_climatology(district_name)
                if climatology_data:
                    # Extract climatology percentiles
                    district, p50_1h, p80_1h, p90_1h, p95_1h, p99_1h, p50_24h, p80_24h, p90_24h, p95_24h, p99_24h, source = climatology_data
                    
                    # Calculate rainfall anomalies (current / climatological percentile)
                    rain_1h_anomaly = rain_1h / max(p95_1h, 1.0)  # Avoid division by zero
                    rain_24h_anomaly = rain_24h / max(p95_24h, 1.0)
                    
                    logger.info(f"CLIMATOLOGY {district_name}: 1h={rain_1h:.1f}mm (P95={p95_1h:.1f}, anomaly={rain_1h_anomaly:.2f}), "
                              f"24h={rain_24h:.1f}mm (P95={p95_24h:.1f}, anomaly={rain_24h_anomaly:.2f})")
                else:
                    logger.warning(f"No climatology data found for {district_name}, using global thresholds")
            except Exception as e:
                logger.error(f"Error accessing climatology for {district_name}: {e}")
        
        # Enhanced risk calculation using both global thresholds and climatology anomalies
        # Apply demo mode sensitivity
        effective_rainfall = rainfall_mm * (ALERT_SENSITIVITY_MULTIPLIER if DEMO_MODE else 1.0)
        
        # Method 1: Traditional global thresholds
        global_risk = 0.0
        if effective_rainfall >= ALERT_THRESHOLDS["rainfall"]["critical"]:
            global_risk = 0.9
            alert_type = "Flash Flood Warning"
            severity = "Critical"
        elif effective_rainfall >= ALERT_THRESHOLDS["rainfall"]["high"]:
            global_risk = 0.7
            alert_type = "Heavy Rainfall Alert"
            severity = "High"
        elif effective_rainfall >= ALERT_THRESHOLDS["rainfall"]["moderate"]:
            global_risk = 0.5
            alert_type = "Rainfall Advisory"
            severity = "Moderate"
        
        # Method 2: Climatology-based anomaly assessment
        anomaly_risk = 0.0
        if climatology_data:
            # Critical: Exceeds P99 (return period ~100 years)
            if rain_1h_anomaly >= (p99_1h / max(p95_1h, 1.0)) or rain_24h_anomaly >= (p99_24h / max(p95_24h, 1.0)):
                anomaly_risk = 0.95
                alert_type = "Extreme Rainfall Emergency"
                severity = "Critical"
            # High: Exceeds P95 significantly (return period ~20 years)
            elif rain_1h_anomaly >= 1.25 or rain_24h_anomaly >= 1.25:
                anomaly_risk = 0.8
                alert_type = "Flash Flood Warning"
                severity = "High"
            # Moderate: Exceeds P95 (return period ~20 years)
            elif rain_1h_anomaly >= 1.0 or rain_24h_anomaly >= 1.0:
                anomaly_risk = 0.65
                alert_type = "Heavy Rainfall Alert"
                severity = "High"
            # Watch: Exceeds P90 (return period ~10 years)
            elif rain_1h_anomaly >= (p90_1h / max(p95_1h, 1.0)) or rain_24h_anomaly >= (p90_24h / max(p95_24h, 1.0)):
                anomaly_risk = 0.5
                alert_type = "Rainfall Advisory"
                severity = "Moderate"
            # Advisory: Exceeds P80 (return period ~5 years)
            elif rain_1h_anomaly >= (p80_1h / max(p95_1h, 1.0)) or rain_24h_anomaly >= (p80_24h / max(p95_24h, 1.0)):
                anomaly_risk = 0.35
                alert_type = "Rainfall Watch"
                severity = "Moderate"
        
        # Combine global and anomaly risks (take the maximum for conservative approach)
        base_risk = max(global_risk, anomaly_risk)
        
        # Combine with ML prediction
        final_risk = base_risk * (1 - ML_PREDICTION_WEIGHT) + ml_prediction * ML_PREDICTION_WEIGHT
        
        # In demo mode, add enhanced sensitivity (deterministic, no randomness)
        if DEMO_MODE and final_risk < 0.4:
            # Deterministic demo enhancement - no randomness
            if rainfall_mm > 5.0:
                final_risk = max(0.6, final_risk + 0.3)
                alert_type = "Heavy Rainfall Alert"
                severity = "Moderate"
            elif rainfall_mm > 2.0:
                final_risk = max(0.4, final_risk + 0.2)
                alert_type = "Rainfall Advisory"
                severity = "Moderate"
        
        return final_risk, alert_type, severity, rain_1h_anomaly, rain_24h_anomaly
    
    def calculate_temperature_risk(self, temperature, ml_prediction=0.0):
        """Calculate temperature-based risk"""
        base_risk = 0.0
        alert_type = None
        severity = "Low"
        
        if temperature >= ALERT_THRESHOLDS["temperature"]["heat_high"]:
            base_risk = 0.8
            alert_type = "Extreme Heat Warning"
            severity = "High"
        elif temperature >= ALERT_THRESHOLDS["temperature"]["heat_moderate"]:
            base_risk = 0.6
            alert_type = "Heat Wave Alert"
            severity = "Moderate"
        elif temperature <= ALERT_THRESHOLDS["temperature"]["cold_high"]:
            base_risk = 0.8
            alert_type = "Severe Cold Warning"
            severity = "High"
        elif temperature <= ALERT_THRESHOLDS["temperature"]["cold_moderate"]:
            base_risk = 0.6
            alert_type = "Cold Wave Alert"
            severity = "Moderate"
        
        final_risk = base_risk * (1 - ML_PREDICTION_WEIGHT) + ml_prediction * ML_PREDICTION_WEIGHT
        return final_risk, alert_type, severity
    
    def calculate_wind_risk(self, wind_speed, ml_prediction=0.0):
        """Calculate wind-based risk"""
        base_risk = 0.0
        alert_type = None
        severity = "Low"
        
        effective_wind = wind_speed * (ALERT_SENSITIVITY_MULTIPLIER if DEMO_MODE else 1.0)
        
        if effective_wind >= ALERT_THRESHOLDS["wind_speed"]["critical"]:
            base_risk = 0.9
            alert_type = "Storm Warning"
            severity = "Critical"
        elif effective_wind >= ALERT_THRESHOLDS["wind_speed"]["high"]:
            base_risk = 0.7
            alert_type = "High Wind Alert"
            severity = "High"
        elif effective_wind >= ALERT_THRESHOLDS["wind_speed"]["moderate"]:
            base_risk = 0.5
            alert_type = "Wind Advisory"
            severity = "Moderate"
        
        final_risk = base_risk * (1 - ML_PREDICTION_WEIGHT) + ml_prediction * ML_PREDICTION_WEIGHT
        return final_risk, alert_type, severity
    
    def calculate_combined_risk(self, weather_data, ml_prediction=0.0, precip_data=None):
        """Calculate combined risk using deterministic HP-specific thresholds"""
        rainfall = weather_data.get('rainfall', 0)
        temperature = weather_data.get('temperature', 20)
        wind_speed = weather_data.get('wind_speed', 0)
        humidity = weather_data.get('humidity', 50)
        
        # Get precipitation accumulation data if available
        rainfall_1h = precip_data.get('rainfall_1h', rainfall) if precip_data else rainfall
        rainfall_3h = precip_data.get('rainfall_3h', rainfall * 3) if precip_data else rainfall * 3
        rainfall_24h = precip_data.get('rainfall_24h', rainfall * 24) if precip_data else rainfall * 24
        api = precip_data.get('api', 0) if precip_data else 0
        
        # Calculate individual risks with enhanced climatology integration
        district_name = weather_data.get('district', 'Unknown')
        rain_risk, rain_alert, rain_severity, rain_1h_anomaly, rain_24h_anomaly = self.calculate_rainfall_risk(
            rainfall, district_name, rainfall_1h, rainfall_24h, ml_prediction)
        temp_risk, temp_alert, temp_severity = self.calculate_temperature_risk(temperature, ml_prediction)
        wind_risk, wind_alert, wind_severity = self.calculate_wind_risk(wind_speed, ml_prediction)
        
        # Deterministic HP-specific thresholds (based on scientific literature)
        landslide_risk = 0.0
        flood_risk = 0.0
        landslide_alert = None
        flood_alert = None
        
        # LANDSLIDE RISK ASSESSMENT (HP-specific)
        # Critical: 1h≥20mm OR 3h≥50mm OR 24h≥100mm + high humidity
        if (rainfall_1h >= 20.0 or rainfall_3h >= 50.0 or rainfall_24h >= 100.0) and humidity > 80:
            landslide_risk = 0.8
            landslide_alert = "Landslide Emergency"
            severity = "Critical"
        # High: Moderate rain + very high humidity + API
        elif (rainfall_1h >= 10.0 or rainfall_3h >= 25.0 or rainfall_24h >= 50.0) and humidity > 85:
            landslide_risk = 0.7
            landslide_alert = "Landslide Warning"
            severity = "High"
        # Moderate: Light rain + high humidity OR high API
        elif (rainfall_1h >= 5.0 or rainfall_3h >= 15.0 or rainfall_24h >= 30.0) and humidity > 80:
            landslide_risk = 0.5
            landslide_alert = "Landslide Watch"
            severity = "Moderate"
        # Watch: High humidity alone (common trigger in HP mountains)
        elif humidity > 90 or (humidity > 85 and api > 10):
            landslide_risk = 0.4
            landslide_alert = "Landslide Advisory"
            severity = "Moderate"
        
        # ENHANCED FLOOD RISK ASSESSMENT (HP-specific)
        # Multiple detection methods for comprehensive flood risk assessment
        district_name = weather_data.get('district', 'Unknown')
        
        # Method 1: Traditional rainfall-based flood risk
        rainfall_flood_risk = 0.0
        if rainfall_3h >= 75.0 or rainfall_24h >= 150.0:
            rainfall_flood_risk = 0.9
        elif (rainfall_3h >= 40.0 or rainfall_24h >= 80.0) and wind_speed > 30:
            rainfall_flood_risk = 0.7
        elif rainfall_3h >= 20.0 or rainfall_24h >= 50.0:
            rainfall_flood_risk = 0.5
        
        # Method 2: Geographic flood zone assessment
        geographic_flood_risk = self._assess_geographic_flood_risk(district_name)
        
        # Method 3: Atmospheric pressure flood risk (sudden pressure drops indicate storms)
        pressure = weather_data.get('pressure', 1013.25)
        atmospheric_flood_risk = self._assess_atmospheric_pressure_risk(pressure, wind_speed)
        
        # Method 4: Enhanced API-based flood risk (accumulated wetness)
        api_flood_risk = self._assess_api_flood_risk(api, humidity)
        
        # Method 5: Soil saturation flood risk
        saturation_flood_risk = self._assess_soil_saturation_risk(humidity, api, temperature)
        
        # Method 6: Snowmelt flood risk (for higher elevations)
        snowmelt_flood_risk = self._assess_snowmelt_risk(district_name, temperature)
        
        # Combine all flood risk factors (take maximum risk)
        all_flood_risks = [
            rainfall_flood_risk,
            geographic_flood_risk, 
            atmospheric_flood_risk,
            api_flood_risk,
            saturation_flood_risk,
            snowmelt_flood_risk
        ]
        
        flood_risk = max(all_flood_risks)
        
        # Determine flood alert type based on combined risk
        if flood_risk >= 0.8:
            flood_alert = "Flash Flood Emergency"
            severity = "Critical"
        elif flood_risk >= 0.6:
            flood_alert = "Flash Flood Warning" 
            severity = "High"
        elif flood_risk >= 0.4:
            flood_alert = "Flood Watch"
            severity = "Moderate"
        elif flood_risk >= 0.3:
            flood_alert = "Flood Advisory"
            severity = "Moderate"
        
        # Combine all risk factors
        risks = [
            (rain_risk, rain_alert, rain_severity),
            (temp_risk, temp_alert, temp_severity),
            (wind_risk, wind_alert, wind_severity),
            (landslide_risk, landslide_alert, "Critical" if landslide_risk > 0.75 else "High" if landslide_risk > 0.6 else "Moderate"),
            (flood_risk, flood_alert, "Critical" if flood_risk > 0.8 else "High" if flood_risk > 0.6 else "Moderate")
        ]
        
        # Filter out zero risks
        active_risks = [(risk, alert, severity) for risk, alert, severity in risks if risk > 0.3 and alert]
        
        if not active_risks:
            return 0.0, None, "Low"
        
        # Return the highest risk
        max_risk, alert_type, severity = max(active_risks, key=lambda x: x[0])
        
        # Apply demo mode sensitivity multiplier (deterministic, no randomness)
        if DEMO_MODE:
            max_risk = min(1.0, max_risk * ALERT_SENSITIVITY_MULTIPLIER)
            logger.info(f"HP ENHANCED: {weather_data.get('district', 'Unknown')} - Risk: {max_risk:.3f}, Alert: {alert_type}, "
                       f"Rainfall(1h/3h/24h): {rainfall_1h:.1f}/{rainfall_3h:.1f}/{rainfall_24h:.1f}mm, "
                       f"Anomalies(1h/24h): {rain_1h_anomaly:.2f}/{rain_24h_anomaly:.2f}, "
                       f"Humidity: {humidity}%, API: {api:.1f}")
        
        return max_risk, alert_type, severity
    
    def process_current_conditions(self):
        """Process current weather conditions using deterministic HP-specific thresholds"""
        logger.info("Processing current weather conditions with enhanced precipitation data...")
        
        # Get latest weather data
        weather_data = get_latest_weather_data()
        if not weather_data:
            logger.warning("No weather data available for risk assessment")
            return {}, []
        
        # Get precipitation accumulation data
        precip_data_raw = get_precipitation_accumulations()
        precip_dict = {}
        for row in precip_data_raw:
            district, timestamp, rainfall_1h, rainfall_3h, rainfall_24h, api, source = row
            precip_dict[district] = {
                'rainfall_1h': rainfall_1h,
                'rainfall_3h': rainfall_3h,
                'rainfall_24h': rainfall_24h,
                'api': api
            }
        
        # Prepare data for ML model (temporarily disabled)
        ml_weather_data = []
        for row in weather_data:
            district, timestamp, temp, rainfall, wind_speed, humidity, pressure, description, source = row
            ml_weather_data.append({
                'location': district,
                'temp': temp,
                'rainfall': rainfall,
                'wind_speed': wind_speed,
                'humidity': humidity,
                'pressure': pressure
            })
        
        # Get ML predictions (currently set to 0 weight)
        ml_predictions = []
        try:
            if ML_PREDICTION_WEIGHT > 0:
                ml_predictions = get_ml_predictions(ml_weather_data)
                logger.info(f"ML predictions received for {len(ml_predictions)} locations")
            else:
                ml_predictions = [0.0] * len(ml_weather_data)
                logger.info("ML predictions disabled - using deterministic thresholds only")
        except Exception as e:
            logger.error(f"Error getting ML predictions: {str(e)}")
            ml_predictions = [0.0] * len(ml_weather_data)
        
        # Process each location with enhanced precipitation data
        risk_assessments = {}
        alerts = []
        
        for i, row in enumerate(weather_data):
            district, timestamp, temp, rainfall, wind_speed, humidity, pressure, description, source = row
            
            weather_dict = {
                'district': district,
                'temperature': temp,
                'rainfall': rainfall,
                'wind_speed': wind_speed,
                'humidity': humidity,
                'pressure': pressure,
                'description': description
            }
            
            # Get precipitation accumulation data for this district
            precip_data = precip_dict.get(district, {
                'rainfall_1h': rainfall,
                'rainfall_3h': rainfall * 3,
                'rainfall_24h': rainfall * 24,
                'api': 0
            })
            
            ml_prediction = ml_predictions[i] if i < len(ml_predictions) else 0.0
            
            # Calculate risk using deterministic thresholds
            risk_score, alert_type, severity = self.calculate_combined_risk(weather_dict, ml_prediction, precip_data)
            
            risk_assessments[district] = {
                'risk_score': risk_score,
                'alert_type': alert_type,
                'severity': severity,
                'ml_prediction': ml_prediction,
                'weather': weather_dict,
                'precipitation': precip_data,
                'timestamp': timestamp
            }
            
            # Generate alert if risk is significant
            alert_threshold = 0.3
            if risk_score > alert_threshold and alert_type:
                alert_message = self.generate_alert_message(district, weather_dict, risk_score, ml_prediction)
                
                alert = {
                    'district': district,
                    'alert_type': alert_type,
                    'severity': severity,
                    'message': alert_message,
                    'risk_score': risk_score,
                    'ml_prediction': ml_prediction,
                    'timestamp': datetime.now()
                }
                
                alerts.append(alert)
                
                # Store alert in database
                insert_alert(district, alert_type, severity, alert_message)
                
                logger.info(f"Alert generated for {district}: {alert_type} ({severity})")
        
        self.current_alerts = alerts
        self.risk_assessments = risk_assessments
        
        logger.info(f"Risk assessment completed: {len(alerts)} alerts generated")
        return risk_assessments, alerts
    
    def generate_alert_message(self, district, weather_data, risk_score, ml_prediction):
        """Generate detailed alert message"""
        temp = weather_data.get('temperature', 0)
        rainfall = weather_data.get('rainfall', 0)
        wind_speed = weather_data.get('wind_speed', 0)
        humidity = weather_data.get('humidity', 0)
        
        message = f"ALERT for {district}: "
        
        if rainfall > 20:
            message += f"Heavy rainfall ({rainfall:.1f}mm/h) detected. "
        elif rainfall > 10:
            message += f"Moderate rainfall ({rainfall:.1f}mm/h) ongoing. "
        
        if wind_speed > 40:
            message += f"Strong winds ({wind_speed:.1f} km/h). "
        elif wind_speed > 25:
            message += f"Moderate winds ({wind_speed:.1f} km/h). "
        
        if temp > 35:
            message += f"High temperature ({temp:.1f}°C). "
        elif temp < 5:
            message += f"Low temperature ({temp:.1f}°C). "
        
        if humidity > 85 and rainfall > 5:
            message += "High landslide risk due to saturated soil conditions. "
        
        message += f"Risk Level: {risk_score:.2f}/1.0. "
        
        if ml_prediction > 0.5:
            message += f"AI model indicates {ml_prediction:.1%} disaster probability. "
        
        message += "Take necessary precautions and stay alert."
        
        return message
    
    def get_current_status(self):
        """Get current alert engine status"""
        return {
            'active_alerts': len(self.current_alerts),
            'monitored_locations': len(self.risk_assessments),
            'last_assessment': datetime.now(),
            'demo_mode': DEMO_MODE,
            'sensitivity_multiplier': ALERT_SENSITIVITY_MULTIPLIER
        }
    
    def get_current_alerts(self):
        """Get currently active alerts"""
        return self.current_alerts
    
    def get_risk_assessments(self):
        """Get current risk assessments"""
        return self.risk_assessments
    
    def _assess_geographic_flood_risk(self, district_name):
        """Assess flood risk based on geographic location and flood-prone zones"""
        # Define flood-prone areas in Himachal Pradesh
        high_flood_risk_areas = {
            'Kangra': 0.6,  # Beas river valley
            'Kullu': 0.5,   # Beas river valley
            'Mandi': 0.7,   # Beas river confluence area
            'Bilaspur': 0.6, # Sutlej river area
            'Hamirpur': 0.5, # Near Beas river
            'Una': 0.4,     # Lower elevation, river proximity
            'Solan': 0.3,   # Moderate elevation
            'Sirmaur': 0.4, # Yamuna tributary area
        }
        
        moderate_flood_risk_areas = {
            'Shimla': 0.3,  # Higher elevation but still has rivers
            'Chamba': 0.4,  # Ravi river valley
            'Dharamshala': 0.3, # Elevated but near rivers
        }
        
        low_flood_risk_areas = {
            'Lahaul and Spiti': 0.2,  # High altitude, cold desert
            'Kinnaur': 0.2,  # High altitude
        }
        
        # Check district flood risk
        if district_name in high_flood_risk_areas:
            return high_flood_risk_areas[district_name]
        elif district_name in moderate_flood_risk_areas:
            return moderate_flood_risk_areas[district_name]
        elif district_name in low_flood_risk_areas:
            return low_flood_risk_areas[district_name]
        else:
            return 0.2  # Default moderate risk for unlisted areas
    
    def _assess_atmospheric_pressure_risk(self, pressure, wind_speed):
        """Assess flood risk based on atmospheric pressure changes"""
        # Normal atmospheric pressure at sea level: 1013.25 hPa
        # Low pressure systems can indicate incoming storms
        
        if pressure < 980:  # Very low pressure
            pressure_risk = 0.7
        elif pressure < 1000:  # Low pressure
            pressure_risk = 0.5
        elif pressure < 1010:  # Slightly low pressure
            pressure_risk = 0.3
        else:
            pressure_risk = 0.0
        
        # Combine with wind speed (high wind + low pressure = storm system)
        if wind_speed > 40 and pressure < 1000:
            pressure_risk = min(0.8, pressure_risk + 0.2)
        elif wind_speed > 25 and pressure < 1005:
            pressure_risk = min(0.6, pressure_risk + 0.1)
        
        return pressure_risk
    
    def _assess_api_flood_risk(self, api, humidity):
        """Assess flood risk based on Antecedent Precipitation Index"""
        # API indicates soil moisture from recent rainfall
        # High API + high humidity = saturated conditions prone to flooding
        
        api_risk = 0.0
        
        if api > 50:  # Very high accumulated precipitation
            api_risk = 0.6
        elif api > 30:  # High accumulated precipitation
            api_risk = 0.4
        elif api > 15:  # Moderate accumulated precipitation
            api_risk = 0.3
        elif api > 5:   # Low accumulated precipitation
            api_risk = 0.2
        
        # Enhance risk if humidity is also high (indicates saturation)
        if humidity > 90 and api > 10:
            api_risk = min(0.7, api_risk + 0.2)
        elif humidity > 85 and api > 5:
            api_risk = min(0.5, api_risk + 0.1)
        
        return api_risk
    
    def _assess_soil_saturation_risk(self, humidity, api, temperature):
        """Assess flood risk based on soil saturation levels"""
        # Soil saturation depends on humidity, recent precipitation, and temperature
        
        saturation_risk = 0.0
        
        # Base saturation from humidity
        if humidity > 95:
            saturation_risk = 0.5
        elif humidity > 90:
            saturation_risk = 0.4
        elif humidity > 85:
            saturation_risk = 0.3
        elif humidity > 80:
            saturation_risk = 0.2
        
        # Enhance with API (recent accumulated moisture)
        if api > 20:
            saturation_risk = min(0.6, saturation_risk + 0.2)
        elif api > 10:
            saturation_risk = min(0.5, saturation_risk + 0.1)
        
        # Temperature factor (moderate temps increase saturation risk)
        if 15 <= temperature <= 25:  # Optimal range for soil saturation
            saturation_risk = min(0.7, saturation_risk + 0.1)
        
        return saturation_risk
    
    def _assess_snowmelt_risk(self, district_name, temperature):
        """Assess flood risk from snowmelt in higher elevation areas"""
        # Higher elevation districts are prone to snowmelt flooding
        
        high_elevation_districts = {
            'Lahaul and Spiti': 0.8,
            'Kinnaur': 0.7,
            'Shimla': 0.5,
            'Kullu': 0.6,
            'Chamba': 0.4,
            'Manali': 0.7
        }
        
        if district_name not in high_elevation_districts:
            return 0.0  # No snowmelt risk for lower elevations
        
        elevation_factor = high_elevation_districts[district_name]
        snowmelt_risk = 0.0
        
        # Snowmelt risk increases with warming temperatures
        if 10 <= temperature <= 20:  # Rapid snowmelt range
            snowmelt_risk = elevation_factor * 0.6
        elif 5 <= temperature <= 25:  # Moderate snowmelt range
            snowmelt_risk = elevation_factor * 0.4
        elif temperature > 25:  # Intense snowmelt
            snowmelt_risk = elevation_factor * 0.8
        
        return min(0.7, snowmelt_risk)
