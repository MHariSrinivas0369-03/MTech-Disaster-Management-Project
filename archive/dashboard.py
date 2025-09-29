"""
Streamlit Dashboard for Himachal Pradesh Disaster Alert System
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import folium
from streamlit_folium import st_folium
import json

from database import get_latest_weather_data, get_active_alerts, get_volunteers, get_tasks
from scheduler import get_status, force_update, assign_volunteer_manually
from config import HP_DISTRICTS, HP_ENHANCED_LOCATIONS

def create_alert_map():
    """Create an interactive map showing alerts and volunteers"""
    # Create base map centered on Himachal Pradesh
    m = folium.Map(location=[31.5, 77.0], zoom_start=8)
    
    # Get current alerts
    alerts = get_active_alerts()
    
    # Get volunteers
    volunteers = get_volunteers()
    
    # Add district markers
    all_locations = HP_DISTRICTS + HP_ENHANCED_LOCATIONS
    location_coords = {loc['name']: (loc['lat'], loc['lon']) for loc in all_locations}
    
    # Add alert markers
    for alert in alerts:
        district, alert_type, severity, message, timestamp = alert
        if district in location_coords:
            lat, lon = location_coords[district]
            
            # Color based on severity
            color = {
                'Critical': 'red',
                'Emergency': 'darkred',
                'High': 'orange',
                'Moderate': 'yellow',
                'Low': 'green'
            }.get(severity, 'blue')
            
            folium.Marker(
                [lat, lon],
                popup=f"<b>{alert_type}</b><br>{district}<br>{severity}<br>{timestamp}",
                tooltip=f"{alert_type} - {severity}",
                icon=folium.Icon(color=color, icon='warning-sign')
            ).add_to(m)
    
    # Add volunteer markers
    for volunteer in volunteers:
        vol_id, name, phone, district, skills, status, registered_at, workload, lat, lon = volunteer
        
        # Color based on status
        color = {
            'available': 'green',
            'assigned': 'orange',
            'en route': 'blue',
            'on-site': 'purple'
        }.get(status, 'gray')
        
        skills_list = json.loads(skills) if skills else []
        skills_text = ', '.join(skills_list)
        
        folium.CircleMarker(
            [lat, lon],
            radius=8,
            popup=f"<b>{name}</b><br>Status: {status}<br>Skills: {skills_text}<br>Workload: {workload}",
            tooltip=f"{name} - {status}",
            color=color,
            fill=True,
            fillOpacity=0.7
        ).add_to(m)
    
    return m

def display_weather_dashboard():
    """Display current weather conditions"""
    st.subheader("🌤️ Current Weather Conditions")
    
    weather_data = get_latest_weather_data()
    if not weather_data:
        st.warning("No weather data available")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(weather_data)
    if not df.empty:
        df.columns = [
            'District', 'Timestamp', 'Temperature', 'Rainfall', 
            'Wind Speed', 'Humidity', 'Pressure', 'Description', 'Source'
        ]
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_temp = df['Temperature'].mean()
        st.metric("Avg Temperature", f"{avg_temp:.1f}°C")
    
    with col2:
        total_rainfall = df['Rainfall'].sum()
        st.metric("Total Rainfall", f"{total_rainfall:.1f}mm")
    
    with col3:
        max_wind = df['Wind Speed'].max()
        st.metric("Max Wind Speed", f"{max_wind:.1f}km/h")
    
    with col4:
        avg_humidity = df['Humidity'].mean()
        st.metric("Avg Humidity", f"{avg_humidity:.1f}%")
    
    # Display weather table
    st.dataframe(df, use_container_width=True)

def display_alerts_dashboard():
    """Display active alerts"""
    st.subheader("🚨 Active Alerts")
    
    alerts = get_active_alerts()
    if not alerts:
        st.success("No active alerts - All conditions normal")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(alerts)
    if not df.empty:
        df.columns = [
            'District', 'Alert Type', 'Severity', 'Message', 'Timestamp'
        ]
    
    # Color code by severity
    def color_severity(val):
        colors = {
            'Critical': 'background-color: #ff4444',
            'Emergency': 'background-color: #ff6666',
            'High': 'background-color: #ff8800',
            'Moderate': 'background-color: #ffaa00',
            'Low': 'background-color: #ffdd00'
        }
        return colors.get(val, '')
    
    styled_df = df.style.applymap(color_severity, subset=['Severity'])
    st.dataframe(styled_df, use_container_width=True)
    
    # Alert summary
    severity_counts = df['Severity'].value_counts()
    st.bar_chart(severity_counts)

def display_volunteers_dashboard():
    """Display volunteer information and assignment interface"""
    st.subheader("👥 Volunteer Management")
    
    volunteers = get_volunteers()
    tasks = get_tasks()
    
    if not volunteers:
        st.warning("No volunteers registered")
        return
    
    # Convert volunteers to DataFrame
    vol_df = pd.DataFrame(volunteers)
    if not vol_df.empty:
        vol_df.columns = [
            'ID', 'Name', 'Phone', 'District', 'Skills', 'Status', 
            'Registered', 'Workload', 'Latitude', 'Longitude'
        ]
    
    # Volunteer statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_volunteers = len(vol_df)
        st.metric("Total Volunteers", total_volunteers)
    
    with col2:
        available = len(vol_df[vol_df['Status'] == 'available'])
        st.metric("Available", available)
    
    with col3:
        assigned = len(vol_df[vol_df['Status'] == 'assigned'])
        st.metric("Assigned", assigned)
    
    with col4:
        on_site = len(vol_df[vol_df['Status'] == 'on-site'])
        st.metric("On Site", on_site)
    
    # Display volunteers table
    st.dataframe(vol_df[['Name', 'District', 'Status', 'Workload', 'Skills']], use_container_width=True)
    
    # Task assignment interface
    st.subheader("📋 Task Assignment")
    
    if tasks:
        # Convert tasks to DataFrame
        task_df = pd.DataFrame(tasks)
        if not task_df.empty:
            task_df.columns = [
                'ID', 'Title', 'Description', 'District', 'Priority', 
                'Status', 'Created', 'Updated', 'Assigned To'
            ]
        
        # Show unassigned tasks
        unassigned_tasks = task_df[task_df['Assigned To'].isna()]
        
        if len(unassigned_tasks) > 0:
            st.write("**Unassigned Tasks:**")
            
            for _, task in unassigned_tasks.iterrows():
                with st.expander(f"Task #{task['ID']}: {task['Title']}"):
                    st.write(f"**Description:** {task['Description']}")
                    st.write(f"**District:** {task['District']}")
                    st.write(f"**Priority:** {task['Priority']}")
                    st.write(f"**Created:** {task['Created']}")
                    
                    # Available volunteers for this task
                    available_volunteers = vol_df[vol_df['Status'] == 'available']
                    
                    if len(available_volunteers) > 0:
                        volunteer_options = {f"{row['Name']} (ID: {row['ID']})": row['ID'] 
                                           for _, row in available_volunteers.iterrows()}
                        
                        selected_volunteer = st.selectbox(
                            "Assign Volunteer:",
                            options=list(volunteer_options.keys()),
                            key=f"task_{task['ID']}"
                        )
                        
                        if st.button(f"Assign to Task #{task['ID']}", key=f"assign_{task['ID']}"):
                            volunteer_id = volunteer_options[selected_volunteer]
                            if assign_volunteer_manually(volunteer_id, task['ID']):
                                st.success(f"Volunteer assigned successfully!")
                                st.rerun()
                            else:
                                st.error("Failed to assign volunteer")
                    else:
                        st.warning("No available volunteers")
        else:
            st.info("All tasks have been assigned")
        
        # Show all tasks
        st.write("**All Tasks:**")
        st.dataframe(task_df, use_container_width=True)
    else:
        st.info("No tasks created yet")

def display_system_status():
    """Display system status and controls"""
    st.subheader("⚙️ System Status")
    
    status = get_status()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("System Status", "🟢 Running" if status['is_running'] else "🔴 Stopped")
        st.metric("Data Collections", status['collection_count'])
        
        if status['last_collection_time']:
            st.metric("Last Collection", status['last_collection_time'].strftime("%H:%M:%S"))
        
        if status['next_collection_time']:
            st.metric("Next Collection", status['next_collection_time'].strftime("%H:%M:%S"))
    
    with col2:
        st.metric("Collection Interval", f"{status['collection_interval_minutes']} minutes")
        
        alert_status = status.get('alert_engine_status', {})
        st.metric("Active Alerts", alert_status.get('active_alerts', 0))
        st.metric("Monitored Locations", alert_status.get('monitored_locations', 0))
    
    # Force update button
    if st.button("🔄 Force Data Collection", type="primary"):
        with st.spinner("Collecting data and processing alerts..."):
            force_update()
        st.success("Data collection completed!")
        st.rerun()

def display_notifications():
    """Display system notifications"""
    if 'notification_message' in st.session_state and st.session_state.notification_message:
        st.subheader("📢 Recent Notifications")
        
        # Show latest 10 notifications
        recent_notifications = st.session_state.notification_message[-10:]
        
        for i, notification in enumerate(reversed(recent_notifications)):
            st.info(notification)
        
        # Clear notifications button
        if st.button("Clear Notifications"):
            st.session_state.notification_message = []
            st.rerun()

def main():
    """Main dashboard function"""
    st.set_page_config(
        page_title="HP Disaster Alert System",
        page_icon="🚨",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🏔️ Himachal Pradesh Disaster Alert System")
    st.markdown("*A Hybrid Geo-spatial Disaster Prediction and Response Framework*")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Select Page", [
        "🗺️ Map Overview",
        "🌤️ Weather Dashboard", 
        "🚨 Alerts",
        "👥 Volunteers",
        "⚙️ System Status"
    ])
    
    # Display notifications
    display_notifications()
    
    # Main content based on selected page
    if page == "🗺️ Map Overview":
        st.subheader("🗺️ Real-time Alert & Volunteer Map")
        
        # Create and display map
        map_obj = create_alert_map()
        st_folium(map_obj, width=1200, height=600)
        
        # Legend
        st.markdown("""
        **Map Legend:**
        - 🔴 Red markers: Critical/Emergency alerts
        - 🟠 Orange markers: High severity alerts  
        - 🟡 Yellow markers: Moderate severity alerts
        - 🟢 Green circles: Available volunteers
        - 🟠 Orange circles: Assigned volunteers
        - 🔵 Blue circles: En route volunteers
        - 🟣 Purple circles: On-site volunteers
        """)
        
    elif page == "🌤️ Weather Dashboard":
        display_weather_dashboard()
        
    elif page == "🚨 Alerts":
        display_alerts_dashboard()
        
    elif page == "👥 Volunteers":
        display_volunteers_dashboard()
        
    elif page == "⚙️ System Status":
        display_system_status()

if __name__ == "__main__":
    main()
