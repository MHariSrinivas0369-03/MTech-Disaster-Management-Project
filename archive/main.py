"""
Main entry point for the Himachal Pradesh Disaster Alert System
"""
import streamlit as st
import sys
import os
import logging
from pathlib import Path
import sqlite3

# Add current directory to path for imports
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

# Import all modules
from database import init_database, get_volunteers, generate_volunteers
from scheduler import start_system
from dashboard import main as dashboard_main
from config import NUMBER_OF_VOLUNTEERS, DATABASE_PATH

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('disaster_alert.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def initialize_system():
    """Initialize the complete disaster alert system"""
    try:
        logger.info("Initializing Himachal Pradesh Disaster Alert System...")
        
        # Initialize database
        logger.info("Setting up database...")
        init_database()
        
        # Check if volunteers exist, if not, generate them
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM volunteers")
        volunteer_count = cursor.fetchone()[0]
        conn.close()
        
        if volunteer_count == 0:
            logger.info("No volunteers found. Generating dummy volunteers...")
            generate_volunteers(NUMBER_OF_VOLUNTEERS)
            logger.info(f"✅ Generated {NUMBER_OF_VOLUNTEERS} volunteers.")
        else:
            logger.info(f"Found {volunteer_count} existing volunteers. Skipping generation.")
        
        # Start the monitoring system
        logger.info("Starting monitoring system...")
        start_system()
        
        logger.info("✅ System initialization completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ System initialization failed: {str(e)}")
        return False

def main():
    """Main application entry point"""
    # System initialization
    if not hasattr(st.session_state, 'system_initialized'):
        with st.spinner("Initializing Himachal Pradesh Disaster Alert System..."):
            success = initialize_system()
            st.session_state.system_initialized = success
        
        if success:
            st.success("✅ System initialized successfully!")
        else:
            st.error("❌ System initialization failed. Please check the logs.")
    
    # Run the dashboard
    dashboard_main()

if __name__ == "__main__":
    main()