import streamlit as st
import json
import folium
from streamlit_folium import st_folium
import os

# --- Page Configuration ---
st.set_page_config(
    page_title="Jules Tracker | Project Sanjaya",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Constants ---
LOG_FILE = os.path.join(os.path.dirname(__file__), '..', 'logs', 'session_log.json')

# --- Helper Functions ---
def load_data(file_path):
    """Loads tracking data from the session log."""
    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        return {"events": []}
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {"events": []}

# --- Main Dashboard ---
st.title("🛰️ Jules Tracker — Project Sanjaya")
st.markdown("A live map dashboard showing your movement from VIT → Airport → Flight → Destination → Home.")

# --- Data Loading ---
data = load_data(LOG_FILE)
events = data.get("events", [])
coords = [(e["lat"], e["lon"]) for e in events if "lat" in e and "lon" in e]

# --- Map Visualization ---
st.header("Live Location Map")

if not coords:
    st.warning("No location data yet. Start the tracker to see your path.")
    # Display a default map of a known location if no data is available
    m = folium.Map(location=[12.9716, 77.5946], zoom_start=10) # Default to Bangalore
else:
    # Create a map centered on the last known coordinate
    m = folium.Map(location=coords[-1], zoom_start=13, tiles="CartoDB positron")

    # Add a polyline to connect the points
    folium.PolyLine(
        locations=coords,
        color="#3498db",  # Blue line
        weight=4,
        opacity=0.8
    ).add_to(m)

    # Add markers for each recorded point
    for i, (lat, lon) in enumerate(coords):
        event = events[i]
        popup_html = f"""
        <b>Point {i+1}</b><br>
        <b>Time:</b> {event.get('timestamp', 'N/A')}<br>
        <b>Lat:</b> {lat:.4f}, <b>Lon:</b> {lon:.4f}
        """
        folium.CircleMarker(
            location=[lat, lon],
            radius=5,
            color="#e74c3c",  # Red marker
            fill=True,
            fill_color="#e74c3c",
            fill_opacity=0.9,
            popup=folium.Popup(popup_html, max_width=200)
        ).add_to(m)

# Display the map
st_folium(m, width="100%", height=500, returned_objects=[])

# --- Status & Data Display ---
st.header("Session Details")

if events:
    last_event = events[-1]
    st.metric(
        label="📍 Last Update",
        value=last_event.get("timestamp", "N/A").replace("T", " ").split(".")[0] + " UTC"
    )
    st.write(f"**Coordinates:** `{last_event['lat']:.5f}, {last_event['lon']:.5f}`")
else:
    st.info("Waiting for first location point...")

# Display raw data in an expander
with st.expander("Show Raw Log Data"):
    st.json(data)