import streamlit as st
from streamlit_autorefresh import st_autorefresh
import json
import folium
from streamlit_folium import st_folium
import os
import sys
import requests
from datetime import datetime, timezone, timedelta
import qrcode
from io import BytesIO

# --- Page Configuration ---
st.set_page_config(
    page_title="Jules Tracker | Project Sanjaya",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Constants ---
TRIP_INFO_FILE = os.path.join(os.path.dirname(__file__), '..', 'logs', 'trip_info.json')
TRIP_LOG_FILE = os.path.join(os.path.dirname(__file__), '..', 'logs', 'trip_log.json')
MAP_IMAGE_FILE = os.path.join(os.path.dirname(__file__), '..', 'logs', 'final_trip_map.png')

# --- Helper Functions ---
def load_json(file_path):
    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        return {}
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def to_ist(utc_dt_str):
    """Converts a UTC isoformat string to a user-friendly IST string."""
    try:
        utc_dt = datetime.fromisoformat(utc_dt_str.replace("Z", "+00:00"))
        ist_dt = utc_dt.astimezone(timezone(timedelta(hours=5, minutes=30)))
        return ist_dt.strftime('%Y-%m-%d %H:%M:%S IST')
    except (ValueError, TypeError):
        return "N/A"

# --- Main Dashboard ---
st.title("🛰️ Jules Tracker — Project Sanjaya (Keystone)")
st.markdown("Live trip tracking with automated flight detection and multi-segment journey support.")

# --- Auto-refresh for active monitoring ---
trip_info = load_json(TRIP_INFO_FILE)
if not trip_info or trip_info.get("trip_status") == "active":
    st_autorefresh(interval=20 * 1000, key="dashboard_refresh")

# --- Data Loading ---
trip_log = load_json(TRIP_LOG_FILE)
events = trip_log.get("events", [])
coords = [(e["lat"], e["lon"]) for e in events if "lat" in e and "lon" in e]

# --- Sidebar ---
st.sidebar.title("Trip Details")

if not trip_info:
    st.sidebar.warning("No active trip. Start a new trip from the web link below.")
else:
    status_map = {
        "active": ("🟢 Active", "https://i.gifer.com/ZZ5H.gif"),
        "ended": ("🔴 Ended", "https://i.gifer.com/56Ab.gif"),
        "at_airport": ("✈️ At Airport", "https://i.gifer.com/origin/f6/f67139d3c636f26b2786377749a3795b.gif"),
        "in_flight": ("🛫 In Flight", "https://i.gifer.com/56Ab.gif"),
        "landed": ("🛬 Landed", "https://i.gifer.com/origin/f6/f67139d3c636f26b2786377749a3795b.gif"),
        "home": ("🏠 Home", "https://i.gifer.com/6E2.gif"),
        "scheduled": ("🗓️ Scheduled", None),
        "pending_schedule": ("⏳ Pending Schedule", None),
        "schedule_failed": ("⚠️ Schedule Failed", None)
    }
    trip_status_text, trip_status_gif = status_map.get(trip_info.get("trip_status"), ("❓ Unknown", None))
    flight_status_text, _ = status_map.get(trip_info.get("flight_info", {}).get("status"), ("❓ Unknown", None))

    st.sidebar.metric("Trip Status", trip_status_text)
    if trip_status_gif:
        st.sidebar.image(trip_status_gif)
    st.sidebar.info(f"**Flight Status:** {flight_status_text}")
    st.sidebar.subheader(f"👋 {trip_info.get('user_name', 'Guest')}")
    st.sidebar.write(f"**Flight:** {trip_info.get('flight_number', 'N/A')}")
    st.sidebar.write(f"**PNR:** {trip_info.get('pnr', 'N/A')}")
    st.sidebar.write(f"**Trip Started:** {to_ist(trip_info.get('trip_start_time'))}")
    if trip_info.get('trip_status') == 'ended':
        st.sidebar.write(f"**Trip Ended:** {to_ist(trip_info.get('trip_end_time'))}")

# --- Map Visualization ---
st.header("Live Journey Map")

if not coords:
    st.info("No location data yet for this trip.")
    m = folium.Map(location=[20.5937, 78.9629], zoom_start=5)
else:
    m = folium.Map(location=coords[-1], zoom_start=13, tiles="CartoDB positron")
    ground_coords = [(e['lat'], e['lon']) for e in events if e.get('source') == 'web']
    flight_coords = [(e['lat'], e['lon']) for e in events if e.get('source') == 'flight']
    if ground_coords: folium.PolyLine(ground_coords, color="#3498db", weight=5, popup="Ground Path").add_to(m)
    if flight_coords: folium.PolyLine(flight_coords, color="#f39c12", weight=4, dash_array='10, 5', popup="Flight Path").add_to(m)
    folium.Marker(location=coords[0], popup="Trip Start", icon=folium.Icon(color='green', icon='play')).add_to(m)
    folium.Marker(location=coords[-1], popup=f"Last Location\n{to_ist(events[-1]['timestamp'])}", icon=folium.Icon(color='red', icon='user')).add_to(m)
    m.fit_bounds(m.get_bounds(), padding=(50, 50))

st_folium(m, width="100%", height=500)

# --- Summary & Data ---
if trip_info.get('trip_status') == 'ended':
    st.header("Trip Summary")
    if os.path.exists(MAP_IMAGE_FILE):
        st.image(MAP_IMAGE_FILE, caption="Final Trip Map")
    else:
        st.warning("Final map image not generated yet.")

with st.expander("Show Raw Log Data"):
    st.json(trip_log)
with st.expander("Show Trip Info"):
    st.json(trip_info)

# --- Sidebar Bottom ---
st.sidebar.markdown("---")
try:
    public_url = sys.argv[1]
    st.sidebar.subheader("📲 Your Public Tracking Link")
    st.sidebar.code(public_url)
    qr_img = qrcode.make(public_url)
    buf = BytesIO()
    qr_img.save(buf, format="PNG")
    st.sidebar.image(buf, width=200, caption="Scan to open tracking page")
except IndexError:
    st.sidebar.warning("Tracking URL not available. Run via `run_app.py`.")

st.sidebar.markdown("---")
# --- Admin Actions ---
is_admin = st.query_params.get("a") == "neelaksh"

if is_admin:
    st.sidebar.subheader("Admin Actions")
    if st.sidebar.button("🗑️ Reset Trip Data"):
        try:
            response = requests.post("http://localhost:5000/reset_trip")
            if response.ok:
                st.sidebar.success("Trip data has been reset!")
                time.sleep(1)
                st.rerun()
            else:
                st.sidebar.error("Failed to reset trip.")
        except requests.exceptions.ConnectionError:
            st.sidebar.error("Could not connect to the backend.")
else:
    st.sidebar.info("Add `?a=neelaksh` to the URL for admin actions like resetting a trip.")