"""
Streamlit Dashboard for Himachal Pradesh Disaster Alert System
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import folium
from streamlit_folium import st_folium
import json
from folium.plugins import MarkerCluster

# Import our modules
from database import (
    init_database, get_latest_weather_data, get_active_alerts, 
    get_volunteers, create_task, get_tasks, assign_volunteer_to_task, get_nearby_volunteers, get_task
)
from scheduler import scheduler, start_system, stop_system, get_status, force_update, assign_volunteer_manually
from config import HP_DISTRICTS, HP_ENHANCED_LOCATIONS


# Initialize database
init_database()

# Page configuration
st.set_page_config(
    page_title="HP Disaster Alert System",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
.metric-container {
    background-color: #f0f2f6;
    padding: 1rem;
    border-radius: 0.5rem;
    margin: 0.5rem 0;
}
.alert-critical {
    background-color: #ffebee;
    border-left: 4px solid #f44336;
    padding: 1rem;
    margin: 0.5rem 0;
}
.alert-high {
    background-color: #fff3e0;
    border-left: 4px solid #ff9800;
    padding: 1rem;
    margin: 0.5rem 0;
}
.alert-moderate {
    background-color: #f3e5f5;
    border-left: 4px solid #9c27b0;
    padding: 1rem;
    margin: 0.5rem 0;
}
.stTabs [data-baseweb="tab-list"] {
    gap: 20px;
}
.stTabs [data-baseweb="tab"] {
    height: 50px;
    white-space: pre-wrap;
    background-color: #f0f2f6;
    border-radius: 5px 5px 0px 0px;
    gap: 1px;
    padding-top: 10px;
    padding-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

def main():
    """Main dashboard application"""
    
    st.title("🚨 Himachal Pradesh Disaster Alert System")
    st.markdown("🎯 **Smart Disaster Prediction & Hybrid Response System**")
    
    # Check for and display live notifications from the scheduler
    if 'notification_message' in st.session_state and st.session_state.notification_message:
        for msg in st.session_state.notification_message:
            if "✅" in msg:
                st.success(msg)
            elif "ℹ️" in msg:
                st.info(msg)
            else:
                st.warning(msg)
        st.session_state.notification_message = []
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page",
        ["Dashboard", "Weather Monitoring", "Active Alerts", "Volunteer Management", "System Control"]
    )
    
    # System status in sidebar
    with st.sidebar:
        st.markdown("---")
        st.subheader("System Status")
        system_status = get_status()
        
        if system_status['is_running']:
            st.success("✅ System Active")
        else:
            st.error("❌ System Stopped")
        
        st.metric("Data Collections", system_status['collection_count'])
        
        if system_status['last_collection_time']:
            time_diff = datetime.now() - system_status['last_collection_time']
            st.metric("Last Update", f"{int(time_diff.total_seconds() / 60)} min ago")
    
    # Route to different pages
    if page == "Dashboard":
        show_dashboard()
    elif page == "Weather Monitoring":
        show_weather_monitoring()
    elif page == "Active Alerts":
        show_active_alerts()
    elif page == "Volunteer Management":
        show_volunteer_management()
    elif page == "System Control":
        show_system_control()

def show_dashboard():
    """Main dashboard overview"""
    st.header("📊 System Overview")
    
    # Get current data
    weather_data = get_latest_weather_data()
    active_alerts = get_active_alerts()
    volunteers = get_volunteers()
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_locations = len(HP_DISTRICTS) + len(HP_ENHANCED_LOCATIONS)
        st.metric("Monitoring Locations", f"{total_locations}")
    
    with col2:
        st.metric("Active Alerts", len(active_alerts))
    
    with col3:
        st.metric("Registered Volunteers", len(volunteers))
    
    with col4:
        available_volunteers = len([v for v in volunteers if v[5] == 'available']) if volunteers else 0
        st.metric("Available Volunteers", available_volunteers)
    
    st.subheader("🗺️ Current Weather & Volunteer Map")
    if weather_data and volunteers:
        show_weather_map(weather_data, volunteers)
    else:
        st.info("No weather data or volunteers available. Please check the data collection system and ensure volunteers are generated.")
    
    # Recent alerts
    if active_alerts:
        st.subheader("🚨 Active Alerts")
        for alert in active_alerts[:5]:
            district, alert_type, severity, message, timestamp = alert
            
            css_class = f"alert-{severity.lower()}"
            st.markdown(f"""
            <div class="{css_class}">
                <strong>{district} - {alert_type}</strong><br>
                <small>{severity} Alert - {timestamp}</small><br>
                {message[:200]}...
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("✅ No active alerts - All districts are in normal conditions")

def show_weather_map(weather_data, volunteers):
    """Display enhanced interactive weather map with location-specific intelligence and volunteers"""
    m = folium.Map(location=[31.1048, 77.1734], zoom_start=8)
    
    # Create a MarkerCluster for volunteers
    volunteer_cluster = MarkerCluster(name="Volunteers").add_to(m)
    
    # Add weather markers
    for record in weather_data:
        district, timestamp, temp, rainfall, wind_speed, humidity, pressure, description, source = record
        
        location_coords = next((d for d in HP_DISTRICTS + HP_ENHANCED_LOCATIONS if d['name'] == district), None)
        if not location_coords: continue
        
        location_info = next((d for d in HP_ENHANCED_LOCATIONS if d['name'] == district), {'type': 'district', 'risk_factors': [], 'elevation': 0})
        
        color = 'green'
        risk_level = 'Normal'
        if rainfall and rainfall >= 25: color, risk_level = 'red', 'Critical'
        elif temp and (temp <= 0 or temp >= 45): color, risk_level = 'red', 'Critical'
        elif wind_speed and wind_speed >= 20: color, risk_level = 'red', 'High'
        elif rainfall and rainfall >= 10: color, risk_level = 'orange', 'Moderate'
        elif wind_speed and wind_speed >= 15: color, risk_level = 'orange', 'Moderate'
        elif rainfall and rainfall >= 5 and location_info.get('type') in ['river', 'valley', 'dam_zone']: color, risk_level = 'orange', 'Moderate - Flood Risk'
        elif location_info.get('elevation', 0) > 3000 and temp and temp < 5: color, risk_level = 'orange', 'High Altitude Risk'
        
        popup_content = f"""
        <b>{district}</b><br>
        <i>Type: {location_info.get('type', 'district').replace('_', ' ').title()}</i><br>
        Temperature: {temp}°C<br>
        Rainfall: {rainfall} mm/h<br>
        <b>Risk Level: {risk_level}</b>
        """
        
        marker_icon = 'home'
        if location_info.get('type') == 'river': marker_icon = 'water'
        elif location_info.get('type') == 'highway': marker_icon = 'road'
        
        folium.Marker(
            location=[location_coords['lat'], location_coords['lon']],
            popup=folium.Popup(popup_content, max_width=250),
            icon=folium.Icon(color=color, icon=marker_icon, prefix='fa'),
            tooltip=f"{district} - {risk_level}"
        ).add_to(m)

    # Add volunteer markers to the cluster
    for volunteer in volunteers:
        vol_id, name, phone, district, skills_str, status, registered_at, workload, lat, lon = volunteer
        
        try: vol_skills = json.loads(skills_str)
        except (json.JSONDecodeError, TypeError): vol_skills = skills_str
        skills_text = ", ".join(vol_skills)
        
        popup_content = f"""
        <b>Volunteer: {name}</b><br>
        Status: {status.title()}<br>
        Skills: {skills_text}<br>
        Workload: {workload}
        """
        marker_color = 'blue'
        if status == 'assigned': marker_color = 'orange'
        elif status == 'en route': marker_color = 'darkblue'
        elif status == 'on-site': marker_color = 'green'
        
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_content, max_width=250),
            icon=folium.Icon(color=marker_color, icon='user', prefix='fa'),
            tooltip=f"{name} ({status.title()})"
        ).add_to(volunteer_cluster)

    st_folium(m, width=700, height=500, use_container_width=True)

def show_weather_monitoring():
    """Weather monitoring page"""
    st.header("🌤️ Weather Monitoring")
    
    if st.button("🔄 Refresh Data"): st.rerun()
    
    weather_data = get_latest_weather_data()
    if not weather_data:
        st.warning("No weather data available")
        return
    
    df = pd.DataFrame(weather_data)
    df.columns = ['District', 'Timestamp', 'Temperature', 'Rainfall', 'Wind Speed',
                  'Humidity', 'Pressure', 'Description', 'Source']
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Temperature by District")
        temp_chart = px.bar(df, x='District', y='Temperature', title='Current Temperature (°C)')
        st.plotly_chart(temp_chart, use_container_width=True)
    
    with col2:
        st.subheader("Rainfall by District")
        rain_chart = px.bar(df, x='District', y='Rainfall', title='Current Rainfall (mm/h)')
        st.plotly_chart(rain_chart, use_container_width=True)
    
    st.subheader("📋 Detailed Weather Data")
    st.dataframe(df, use_container_width=True)
    
def show_active_alerts():
    """Active alerts page"""
    st.header("🚨 Active Alerts")
    active_alerts = get_active_alerts()
    
    if not active_alerts:
        st.success("✅ No active alerts - All conditions are normal")
        return
    
    st.warning(f"⚠️ {len(active_alerts)} active alerts require attention")
    
    for i, alert in enumerate(active_alerts):
        district, alert_type, severity, message, timestamp = alert
        with st.expander(f"{district} - {alert_type} ({severity})", expanded=i < 3):
            st.write(f"**Alert Type:** {alert_type}")
            st.write(f"**Severity:** {severity}")
            st.write(f"**Time:** {timestamp}")
            st.write(f"**Message:**")
            st.write(message)
            if st.button(f"✅ Mark as Resolved", key=f"resolve_{i}"): st.success("Alert marked as resolved")

def show_volunteer_management():
    """Volunteer management page"""
    st.header("👥 Volunteer Management")
    
    tab1, tab2 = st.tabs(["Volunteer List", "Task Management"])
    
    with tab1:
        st.subheader("Registered Volunteers")
        
        volunteers = get_volunteers()
        if volunteers:
            volunteer_df = pd.DataFrame(volunteers)
            volunteer_df.columns = ['ID', 'Name', 'Phone', 'District', 'Skills', 'Status', 'Registered', 'Workload', 'Latitude', 'Longitude']
            volunteer_df['Skills'] = volunteer_df['Skills'].apply(json.loads)
            
            st.dataframe(volunteer_df[['ID', 'Name', 'District', 'Skills', 'Workload', 'Status', 'Registered']], use_container_width=True)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1: st.metric("Total Volunteers", len(volunteers))
            with col2: st.metric("Available", len([v for v in volunteers if v[5] == 'available']))
            with col3: st.metric("Assigned", len([v for v in volunteers if v[5] != 'available']))
            with col4: st.metric("Districts Covered", len(pd.DataFrame(volunteers)[3].value_counts()))
        else: st.info("No volunteers registered yet")
    
    with tab2:
        st.subheader("Manual Task Assignment")
        tasks = get_tasks()
        
        if tasks:
            task_df = pd.DataFrame(tasks)
            task_df.columns = ['ID', 'Title', 'Description', 'District', 'Priority', 'Status', 'Created', 'Updated', 'Assigned To']
            pending_tasks = task_df[task_df['Status'] == 'pending']
            
            if not pending_tasks.empty:
                st.info("Select a pending task to manually assign a volunteer.")
                task_to_assign = st.selectbox(
                    "Select Task ID", 
                    options=pending_tasks['ID'], 
                    format_func=lambda x: f"Task #{x} - {pending_tasks[pending_tasks['ID']==x]['Title'].iloc[0]}"
                )

                if task_to_assign:
                    task_info = pending_tasks[pending_tasks['ID'] == task_to_assign].iloc[0]
                    st.write(f"**Selected Task:** {task_info['Title']}")
                    
                    task_coords = next((d for d in HP_DISTRICTS + HP_ENHANCED_LOCATIONS if d['name'] == task_info['District']), None)
                    if task_coords:
                        nearby_volunteers = get_nearby_volunteers(task_coords['lat'], task_coords['lon'])
                        if nearby_volunteers:
                            st.write(f"**Top 3 Recommended Volunteers near {task_info['District']}:**")
                            
                            recommended_volunteers = nearby_volunteers[:3]
                            for i, vol in enumerate(recommended_volunteers):
                                col1, col2 = st.columns([0.7, 0.3])
                                with col1:
                                    st.markdown(f"**{vol['name']}** (Workload: {vol['workload']}, Distance: {vol['distance_km']:.1f}km)<br>_Skills: {', '.join(vol['skills'])}_", unsafe_allow_html=True)
                                with col2:
                                    if st.button(f"Assign", key=f"assign_vol_{vol['id']}_{task_to_assign}"):
                                        if assign_volunteer_manually(vol['id'], task_to_assign):
                                            st.session_state.notification_message.append(f"✅ Volunteer {vol['name']} has been assigned to task #{task_to_assign}.")
                                            st.rerun()
                                        else:
                                            st.error("❌ Failed to assign volunteer.")
                        else: st.warning(f"⚠️ No available volunteers found near {task_info['District']}.")
                    else: st.error(f"❌ Could not find location coordinates for {task_info['District']}.")
            else: st.success("✅ No pending tasks to assign.")
        else: st.info("No tasks created yet.")

def show_system_control():
    """System control page"""
    st.header("⚙️ System Control")
    system_status = get_status()
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("System Status")
        if system_status['is_running']: st.success("✅ System is Active")
        else: st.error("❌ System is Stopped")
        st.metric("Total Data Collections", system_status['collection_count'])
        if system_status['last_collection_time']: st.write(f"**Last Collection:** {system_status['last_collection_time']}")
        if system_status['next_collection_time']: st.write(f"**Next Collection:** {system_status['next_collection_time']}")
    
    with col2:
        st.subheader("System Controls")
        col_start, col_stop = st.columns(2)
        with col_start:
            if st.button("🟢 Start System"): start_system(); st.success("System started!"); st.rerun()
        with col_stop:
            if st.button("🔴 Stop System"): stop_system(); st.warning("System stopped!"); st.rerun()
        if st.button("🔄 Force Data Collection"):
            with st.spinner("Collecting data..."): force_update(); st.success("Data collection completed!"); st.rerun()
    
    if 'alert_engine_status' in system_status:
        st.subheader("🚨 Alert Engine Status")
        alert_status = system_status['alert_engine_status']
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("Districts Monitored", alert_status['total_districts'])
        with col2: st.metric("Active Alerts", alert_status['active_alerts'])
        with col3: st.metric("Last Update", alert_status['last_update'].strftime("%H:%M:%S") if alert_status.get('last_update') else "N/A")
    
    st.subheader("⚙️ Configuration")
    st.write("**Data Collection Interval:**", f"{system_status['collection_interval_minutes']} minutes")
    st.write("**Monitored Districts:**", len(HP_DISTRICTS) + len(HP_ENHANCED_LOCATIONS))
    
    st.text("Note: The SMS service has been removed from this version of the project.")

if __name__ == "__main__":
    main()