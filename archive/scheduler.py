"""
Automated scheduler for data collection and alert processing
"""
import time
import threading
import logging
from datetime import datetime, timedelta
import streamlit as st
import sqlite3
import json

from data_fetcher import DataFetcher
from alert_engine import AlertEngine
from config import DATA_COLLECTION_INTERVAL, HP_DISTRICTS, HP_ENHANCED_LOCATIONS, DATABASE_PATH
from database import get_volunteers, create_task, assign_volunteer_to_task, get_nearby_volunteers, get_latest_weather_data, get_task

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Lock for database operations
db_lock = threading.Lock()

class DisasterAlertScheduler:
    def __init__(self):
        self.data_fetcher = DataFetcher()
        self.alert_engine = AlertEngine()
        self.is_running = False
        self.scheduler_thread = None
        self.last_collection_time = None
        self.collection_count = 0
        
    def start_monitoring(self):
        """Start the automated monitoring system"""
        if self.is_running:
            logger.warning("Monitoring system is already running")
            return
        
        logger.info("Starting Himachal Pradesh Disaster Alert System...")
        logger.info(f"Data collection interval: {DATA_COLLECTION_INTERVAL} minutes")
        
        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("✅ Monitoring system started successfully")
    
    def stop_monitoring(self):
        """Stop the automated monitoring system"""
        if not self.is_running:
            logger.warning("Monitoring system is not running")
            return
        
        logger.info("Stopping monitoring system...")
        self.is_running = False
        
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        
        logger.info("✅ Monitoring system stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop that runs in background"""
        logger.info("Monitoring loop started")
        
        while self.is_running:
            try:
                self._perform_monitoring_cycle()
                
                for _ in range(DATA_COLLECTION_INTERVAL * 60):
                    if not self.is_running:
                        break
                    time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                time.sleep(60)
    
    def _perform_monitoring_cycle(self):
        """Perform one complete monitoring cycle"""
        cycle_start = datetime.now()
        logger.info(f"=== Starting Monitoring Cycle #{self.collection_count + 1} ===")
        
        try:
            # Step 1: Collect weather data from all sources
            logger.info("Step 1: Collecting weather data...")
            self.data_fetcher.collect_all_data()
            
            # Step 2: Process data and assess risks
            logger.info("Step 2: Processing risk assessment...")
            risk_assessments, alerts = self.alert_engine.process_current_conditions()
            
            # Step 3: Process alerts and assign volunteers based on hybrid logic
            if alerts:
                logger.info(f"Step 3: Processing {len(alerts)} alerts...")
                self._process_alerts(alerts)
            else:
                logger.info("Step 3: No alerts to process - all conditions normal")

            # Step 4: Run the simulated "proof of work"
            self._simulate_volunteer_activity()
            
            self.collection_count += 1
            self.last_collection_time = cycle_start
            
            cycle_duration = (datetime.now() - cycle_start).total_seconds()
            logger.info(f"✅ Monitoring cycle completed in {cycle_duration:.2f} seconds")
            logger.info(f"Next collection in {DATA_COLLECTION_INTERVAL} minutes")
            
        except Exception as e:
            logger.error(f"Error in monitoring cycle: {str(e)}")

    def _simulate_volunteer_activity(self):
        """Simulate volunteers changing status from 'assigned' to 'en route' and 'on-site'"""
        with db_lock:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            # Get all assigned volunteers who are not yet 'on-site'
            cursor.execute("SELECT id, name, status, district FROM volunteers WHERE status IN ('assigned', 'en route')")
            volunteers_to_update = cursor.fetchall()
            
            if volunteers_to_update:
                if 'notification_message' not in st.session_state:
                    st.session_state.notification_message = []
                    
                for vol_id, name, status, district in volunteers_to_update:
                    if status == 'assigned':
                        # Change status to 'en route'
                        cursor.execute("UPDATE volunteers SET status = 'en route' WHERE id = ?", (vol_id,))
                        message = f"🚗 Volunteer {name} is en route to {district}."
                        st.session_state.notification_message.append(message)
                        logger.info(f"Volunteer {name} status updated to 'en route'.")
                    elif status == 'en route':
                        # Change status to 'on-site'
                        cursor.execute("UPDATE volunteers SET status = 'on-site' WHERE id = ?", (vol_id,))
                        message = f"✅ Volunteer {name} has arrived at {district} and is assisting."
                        st.session_state.notification_message.append(message)
                        logger.info(f"Volunteer {name} status updated to 'on-site'.")
                
                conn.commit()
            conn.close()

    
    def _process_alerts(self, alerts):
        """Process and assign volunteers based on hybrid logic"""
        for alert in alerts:
            try:
                alert_severity = alert.get('severity')
                alert_district = alert.get('district')
                alert_message = alert.get('message')
                
                logger.info(f"Processing alert: {alert['alert_type']} for {alert_district}")
                
                # Step 1: Create a task for every alert
                task_id = create_task(
                    title=f"{alert['alert_type']} in {alert_district}",
                    description=alert_message,
                    district=alert_district,
                    priority=alert_severity.lower()
                )

                assigned_volunteers = []
                
                # Step 2: Implement hybrid assignment logic
                # Only automatically assign for Critical and Emergency alerts
                if alert_severity in ['Critical', 'Emergency']:
                    location_coords = self._get_location_coordinates(alert_district)

                    if location_coords:
                        nearby_volunteers = get_nearby_volunteers(
                            location_coords['lat'],
                            location_coords['lon'],
                            max_distance_km=25
                        )
                        
                        if nearby_volunteers:
                            # For critical alerts, assign up to 3 nearby volunteers
                            volunteers_to_assign = nearby_volunteers[:3]
                            for vol in volunteers_to_assign:
                                if assign_volunteer_to_task(vol['id'], task_id):
                                    assigned_volunteers.append(vol)
                                    logger.info(f"Critical alert automatically assigned to volunteer {vol['name']} ({vol['id']})")
                
                # Push a notification to the dashboard
                if 'notification_message' not in st.session_state:
                    st.session_state.notification_message = []
                
                if assigned_volunteers:
                    names = ", ".join([v['name'] for v in assigned_volunteers])
                    message = f"✅ Volunteer(s) {names} automatically assigned to task #{task_id} for a {alert['alert_type']} in {alert_district}."
                    st.session_state.notification_message.append(message)
                elif alert_severity in ['Moderate', 'High', 'Low']:
                    message = f"ℹ️ New task #{task_id} created for {alert_district} ({alert['alert_type']}). Awaiting manual volunteer assignment."
                    st.session_state.notification_message.append(message)
                else:
                    message = f"⚠️ No volunteers found to assign for alert in {alert_district}."
                    st.session_state.notification_message.append(message)

                logger.info(f"Alert notifications processed for {alert_district}")
                
            except Exception as e:
                logger.error(f"Error processing alert for {alert_district}: {str(e)}")
    
    def _get_location_coordinates(self, location_name):
        """Helper to find coordinates for a location, handles both districts and enhanced locations"""
        for entry in HP_DISTRICTS + HP_ENHANCED_LOCATIONS:
            if entry['name'] == location_name:
                return entry
        return None

    def force_collection(self):
        """Force immediate data collection and processing"""
        logger.info("Forcing immediate data collection...")
        self._perform_monitoring_cycle()
    
    def get_system_status(self):
        """Get current system status"""
        return {
            'is_running': self.is_running,
            'collection_count': self.collection_count,
            'last_collection_time': self.last_collection_time,
            'next_collection_time': (
                self.last_collection_time + timedelta(minutes=DATA_COLLECTION_INTERVAL)
                if self.last_collection_time else None
            ),
            'collection_interval_minutes': DATA_COLLECTION_INTERVAL,
            'alert_engine_status': self.alert_engine.get_current_status(),
        }

# Global scheduler instance
scheduler = DisasterAlertScheduler()

def start_system():
    """Start the disaster alert system"""
    scheduler.start_monitoring()

def stop_system():
    """Stop the disaster alert system"""
    scheduler.stop_monitoring()

def get_status():
    """Get system status"""
    return scheduler.get_system_status()

def force_update():
    """Force immediate data collection"""
    scheduler.force_collection()

def assign_volunteer_manually(volunteer_id, task_id):
    """
    Manually assign a volunteer to a task, called from the dashboard.
    This simulates the core assignment logic.
    """
    try:
        with db_lock:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            # Update the task with the assigned volunteer
            cursor.execute("UPDATE tasks SET assigned_to = ?, status = ?, updated_at = ? WHERE id = ?", (volunteer_id, 'assigned', datetime.now(), task_id))
            
            # Increase the volunteer's workload and update status
            cursor.execute("UPDATE volunteers SET workload = workload + 1, status = 'assigned' WHERE id = ?", (volunteer_id,))
            conn.commit()
            conn.close()

        volunteers = get_volunteers()
        volunteer = next((v for v in volunteers if v[0] == volunteer_id), None)
        
        if volunteer:
            if 'notification_message' not in st.session_state:
                st.session_state.notification_message = []
            
            message = f"✅ Volunteer {volunteer[1]} manually assigned to task #{task_id}."
            st.session_state.notification_message.append(message)
            return True
    except Exception as e:
        logger.error(f"Error during manual assignment: {e}")
    return False