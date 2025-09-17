"""
Standalone script to populate the database with random volunteers
"""
import sys
import os
import sqlite3
import logging

# Add current directory to path for imports
from pathlib import Path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

# Import database and config modules
from database import init_database, generate_volunteers
from config import NUMBER_OF_VOLUNTEERS, HP_DISTRICTS, HP_ENHANCED_LOCATIONS

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_volunteer_generator():
    """
    Main function to initialize the database and populate it with volunteers.
    """
    logger.info("--- Starting Volunteer Data Generation ---")
    
    # 1. Initialize the database schema
    try:
        init_database()
        logger.info("Database schema initialized successfully.")
    except sqlite3.Error as e:
        logger.error(f"Failed to initialize database: {e}")
        return

    # 2. Get the number of existing volunteers
    conn = sqlite3.connect("disaster_alert.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM volunteers")
    count = cursor.fetchone()[0]
    conn.close()

    if count > 0:
        logger.warning(f"Database already contains {count} volunteers. Skipping generation.")
        logger.warning("To generate new volunteers, please delete the 'disaster_alert.db' file first.")
        return
        
    # 3. Generate and insert random volunteers
    try:
        logger.info(f"Generating {NUMBER_OF_VOLUNTEERS} random volunteers...")
        generated_count = generate_volunteers(NUMBER_OF_VOLUNTEERS)
        logger.info(f"✅ Successfully generated and added {generated_count} volunteers to the database.")
    except Exception as e:
        logger.error(f"An error occurred during volunteer generation: {e}")
    
    logger.info("--- Volunteer Data Generation Completed ---")

if __name__ == "__main__":
    run_volunteer_generator()