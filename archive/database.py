"""
Database operations for the Himachal Pradesh Disaster Alert System
"""
import sqlite3
import json
import random
from datetime import datetime
from geopy.distance import geodesic
from config import DATABASE_PATH, HP_DISTRICTS, HP_ENHANCED_LOCATIONS, VOLUNTEER_NAME_PREFIXES, VOLUNTEER_SKILLS

def init_database():
    """Initialize the SQLite database with required tables"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Weather data table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS weather_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            district TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            temperature REAL,
            rainfall REAL,
            wind_speed REAL,
            humidity REAL,
            pressure REAL,
            weather_description TEXT,
            source TEXT NOT NULL
        )
    ''')
    
    # Alerts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            district TEXT NOT NULL,
            alert_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            status TEXT DEFAULT 'active',
            resolved_at DATETIME
        )
    ''')
    
    # Volunteers table with new attributes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS volunteers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            district TEXT NOT NULL,
            skills TEXT,
            status TEXT DEFAULT 'available',
            workload INTEGER DEFAULT 0,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            registered_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tasks table with assignment tracking
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            district TEXT NOT NULL,
            priority TEXT DEFAULT 'medium',
            status TEXT DEFAULT 'pending',
            assigned_to INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (assigned_to) REFERENCES volunteers (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def generate_volunteers(num_volunteers):
    """
    Generates and inserts a specified number of random volunteers into the database.
    This replaces the manual registration form.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Get a list of all locations (districts and enhanced locations) with coordinates
    all_locations = HP_DISTRICTS + HP_ENHANCED_LOCATIONS
    
    generated_count = 0
    for i in range(num_volunteers):
        try:
            # Generate a random name
            name = f"{random.choice(VOLUNTEER_NAME_PREFIXES)}{i+1}"
            
            # Generate a random Indian phone number (example, not for real use)
            phone = f"+91{random.randint(6000000000, 9999999999)}"
            
            # Randomly select a location for the volunteer
            location_info = random.choice(all_locations)
            district_name = location_info.get('district', location_info['name'])
            
            # Get location coordinates
            lat = location_info['lat'] + random.uniform(-0.1, 0.1) # Add slight randomness
            lon = location_info['lon'] + random.uniform(-0.1, 0.1)
            
            # Randomly assign a set of skills
            num_skills = random.randint(1, 3)
            skills = random.sample(VOLUNTEER_SKILLS, num_skills)
            skills_json = json.dumps(skills)
            
            # Insert the new volunteer
            cursor.execute('''
                INSERT INTO volunteers (name, phone, district, skills, latitude, longitude)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, phone, district_name, skills_json, lat, lon))
            generated_count += 1
        except sqlite3.IntegrityError:
            # This handles the unlikely case of a phone number collision
            continue
    
    conn.commit()
    conn.close()
    return generated_count

def get_nearby_volunteers(target_lat, target_lon, max_distance_km=20):
    """
    Retrieves a list of available volunteers within a specified distance
    of a target location.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, name, phone, district, skills, workload, latitude, longitude
        FROM volunteers
        WHERE status = 'available'
        ORDER BY workload ASC
    ''')
    
    volunteers = cursor.fetchall()
    nearby_volunteers = []
    
    target_coords = (target_lat, target_lon)
    
    for volunteer in volunteers:
        vol_id, name, phone, district, skills, workload, lat, lon = volunteer
        volunteer_coords = (lat, lon)
        
        distance = geodesic(target_coords, volunteer_coords).km
        
        if distance <= max_distance_km:
            nearby_volunteers.append({
                'id': vol_id,
                'name': name,
                'phone': phone,
                'district': district,
                'skills': json.loads(skills),
                'workload': workload,
                'distance_km': distance
            })
            
    conn.close()
    return sorted(nearby_volunteers, key=lambda x: x['workload'])

def assign_volunteer_to_task(volunteer_id, task_id):
    """Assigns a volunteer to a task and updates their workload"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # Update the task with the assigned volunteer
        cursor.execute('''
            UPDATE tasks SET assigned_to = ?, status = ?, updated_at = ?
            WHERE id = ?
        ''', (volunteer_id, 'assigned', datetime.now(), task_id))
        
        # Increase the volunteer's workload
        cursor.execute('''
            UPDATE volunteers SET workload = workload + 1, status = 'assigned'
            WHERE id = ?
        ''', (volunteer_id,))
        
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database error during assignment: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_task(task_id):
    """Get a single task by its ID"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
    task = cursor.fetchone()
    conn.close()
    return task

def insert_weather_data(district, temperature, rainfall, wind_speed, humidity, pressure, description, source):
    """Insert weather data into database"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO weather_data 
        (district, timestamp, temperature, rainfall, wind_speed, humidity, pressure, weather_description, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (district, datetime.now(), temperature, rainfall, wind_speed, humidity, pressure, description, source))
    
    conn.commit()
    conn.close()

def insert_alert(district, alert_type, severity, message):
    """Insert alert into database"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO alerts (district, alert_type, severity, message, timestamp)
        VALUES (?, ?, ?, ?, ?)
    ''', (district, alert_type, severity, message, datetime.now()))
    
    conn.commit()
    conn.close()

def get_active_alerts():
    """Get all active alerts"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT district, alert_type, severity, message, timestamp
        FROM alerts 
        WHERE status = 'active'
        ORDER BY timestamp DESC
    ''')
    
    alerts = cursor.fetchall()
    conn.close()
    return alerts

def get_latest_weather_data():
    """Get latest weather data for all districts"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT w1.district, w1.timestamp, w1.temperature, w1.rainfall, 
               w1.wind_speed, w1.humidity, w1.pressure, w1.weather_description, w1.source
        FROM weather_data w1
        INNER JOIN (
            SELECT district, MAX(timestamp) as max_timestamp
            FROM weather_data
            GROUP BY district
        ) w2 ON w1.district = w2.district AND w1.timestamp = w2.max_timestamp
        ORDER BY w1.district
    ''')
    
    data = cursor.fetchall()
    conn.close()
    return data

def get_volunteers():
    """Get all registered volunteers, including their coordinates"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, name, phone, district, skills, status, registered_at, workload, latitude, longitude
        FROM volunteers
        ORDER BY workload ASC, name
    ''')
    
    volunteers = cursor.fetchall()
    conn.close()
    return volunteers

def create_task(title, description, district, priority="medium"):
    """Create a new task"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO tasks (title, description, district, priority)
        VALUES (?, ?, ?, ?)
    ''', (title, description, district, priority))
    
    conn.commit()
    task_id = cursor.lastrowid
    conn.close()
    return task_id

def get_tasks():
    """Get all tasks with volunteer information"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT t.id, t.title, t.description, t.district, t.priority, 
               t.status, t.created_at, t.updated_at, v.name as volunteer_name
        FROM tasks t
        LEFT JOIN volunteers v ON t.assigned_to = v.id
        ORDER BY t.created_at DESC
    ''')
    
    tasks = cursor.fetchall()
    conn.close()
    return tasks