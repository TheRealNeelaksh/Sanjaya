import streamlit as st
import json
import folium
from streamlit_folium import st_folium
import os
from datetime import datetime

# --- Page Configuration ---
st.set_page_config(
    page_title="Jules Tracker | Project Sanjaya",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Constants ---
LOG_FILE = os.path.join(os.path.dirname(__file__), '..', 'logs', 'session_log.json')
SESSION_INFO_FILE = os.path.join(os.path.dirname(__file__), '..', 'logs', 'session_info.json')

# --- Helper Functions ---
def load_json(file_path):
    """Loads data from a JSON file."""
    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        return {}
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

# --- Main Dashboard ---
st.title("🛰️ Jules Tracker — Project Sanjaya")
st.markdown("Real-time safety tracking with location and flight visualization.")

# --- Auto-refresh ---
# Disabled for now as it can be jarring, but can be enabled if needed.
# st_autorefresh(interval=15000, limit=None, key="dashboard_refresh")

# --- Data Loading ---
session_info = load_json(SESSION_INFO_FILE)
location_data = load_json(LOG_FILE)
events = location_data.get("events", [])
coords = [(e["lat"], e["lon"]) for e in events if "lat" in e and "lon" in e]

# --- Sidebar for Session Info ---
st.sidebar.title(" பயண விவரங்கள் (Trip Details)")

if not session_info:
    st.sidebar.warning("No active session. Start tracking from the web link.")
else:
    status_map = {
        "active": "🟢 Active",
        "stopped": "🔴 Stopped",
        "at_airport": "✈️ At Airport",
        "in_flight": "🛫 In Flight",
        "landed": "🛬 Landed"
    }
    display_status = status_map.get(session_info.get("status", "unknown"), "❓ Unknown")

    st.sidebar.metric("Status", display_status)
    st.sidebar.subheader(f"👋 Welcome, {session_info.get('user_name', 'Guest')}!")
    st.sidebar.info(f"**Flight:** {session_info.get('flight_number', 'N/A')}\n\n**PNR:** {session_info.get('pnr', 'N/A')}")

    start_time_str = session_info.get("start_time", "").replace("Z", "")
    if start_time_str:
        start_time = datetime.fromisoformat(start_time_str)
        st.sidebar.write(f"**Session Started:** {start_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")

# --- Map Visualization ---
st.header("Live Location Map")

if not coords:
    st.warning("No location data yet for this session.")
    m = folium.Map(location=[20.5937, 78.9629], zoom_start=5) # Default to India
else:
    m = folium.Map(location=coords[-1], zoom_start=13, tiles="CartoDB positron")
    folium.PolyLine(locations=coords, color="#3498db", weight=4, opacity=0.8).add_to(m)

    # Start marker
    folium.Marker(
        location=coords[0],
        popup="Trip Start",
        icon=folium.Icon(color='green', icon='play')
    ).add_to(m)

    # Current location marker
    folium.Marker(
        location=coords[-1],
        popup=f"Current Location\n{events[-1]['timestamp']}",
        icon=folium.Icon(color='red', icon='user')
    ).add_to(m)

st_folium(m, width="100%", height=500, returned_objects=[])

# --- Data Display ---
col1, col2 = st.columns(2)
with col1:
    st.metric("Total Points Logged", len(events))
with col2:
    if events:
        last_update_str = events[-1]['timestamp'].replace("Z", "")
        last_update_time = datetime.fromisoformat(last_update_str)
        st.metric("📍 Last Update (UTC)", last_update_time.strftime('%H:%M:%S'))

with st.expander("Show Raw Log Data"):
    st.json(location_data)