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
from jules.utils import get_airport_coords # Import the new function

# --- Page Configuration ---
st.set_page_config(
    page_title="Jules Tracker | Project Sanjaya",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Constants ---
# Get the backend URL from an environment variable, with a default for local dev
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:5000")
MAP_IMAGE_FILE = os.path.join(os.path.dirname(__file__), '..', 'logs', 'final_trip_map.png')

# --- Helper Functions ---
def load_data_from_api():
    """Fetches the latest trip data from the backend API."""
    try:
        api_url = f"{BACKEND_URL}/api/get_trip_data"
        response = requests.get(api_url, timeout=5)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        data = response.json()

        # The API returns an object with 'trip_info' and 'trip_log' keys
        trip_info = data.get("trip_info", {})
        trip_log = data.get("trip_log", {"events": []})

        return trip_info, trip_log

    except requests.exceptions.RequestException:
        # Silently fail on connection errors, returning empty data.
        # This prevents the dashboard from crashing if the backend is temporarily down.
        return {}, {"events": []}
    except json.JSONDecodeError:
        st.error("Error decoding data from the backend.")
        return {}, {"events": []}

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

# --- Data Loading & Auto-Refresh ---
trip_info, trip_log = load_data_from_api()

if not trip_info or trip_info.get("trip_status") == "active":
    st_autorefresh(interval=20 * 1000, key="dashboard_refresh")

events = trip_log.get("events", [])
coords = [(e["lat"], e["lon"]) for e in events if "lat" in e and "lon" in e]

# --- Sidebar ---
st.sidebar.title("Trip Details")

if not trip_info:
    st.sidebar.warning("No active trip. Waiting for data from the backend...")
else:
    # Define paths to local GIFs
    assets_path = os.path.join(os.path.dirname(__file__), 'assets')
    status_map = {
        "active": ("Tracking Active", os.path.join(assets_path, 'online.gif')),
        "ended": ("Trip Ended", os.path.join(assets_path, 'offline.gif')),
        "boarding": ("Boarding", None),
        "in_flight": ("In Flight", os.path.join(assets_path, 'airplane.gif')),
        "landed": ("Landed", os.path.join(assets_path, 'online.gif')),
        "home": ("Home", os.path.join(assets_path, 'home.gif')),
        "scheduled": ("Flight Scheduled", None)
    }

    trip_status = trip_info.get("trip_status", "ended")
    flight_status = trip_info.get("flight_info", {}).get("status")

    # Determine overall status
    display_status = trip_status
    if flight_status == 'in_flight':
        display_status = 'in_flight'
    elif trip_info.get('current_tracking_status') == 'idle' and trip_status == 'active':
        display_status = 'ended' # Represents offline/idle state

    status_text, status_gif_path = status_map.get(display_status, ("Unknown", None))

    st.sidebar.metric("Status", status_text)
    if status_gif_path and os.path.exists(status_gif_path):
        st.sidebar.image(status_gif_path)

    st.sidebar.info(f"**Flight Status:** {status_map.get(flight_status, ('Unknown', None))[0]}")

    flight_info = trip_info.get("flight_info", {})
    if flight_info.get("flight_duration"):
        st.sidebar.write(f"**Est. Duration:** {flight_info['flight_duration']}")
    if flight_info.get("time_left_to_land"):
        st.sidebar.write(f"**Time to Land:** {flight_info['time_left_to_land']}")

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

    # Find pre-flight and post-flight ground coordinates
    dep_time = datetime.fromisoformat(trip_info['flight_info']['scheduled_departure'])
    arr_time = datetime.fromisoformat(trip_info['flight_info']['scheduled_arrival'])

    pre_flight_coords = [ (e['lat'], e['lon']) for e in events if datetime.fromisoformat(e['timestamp']) < dep_time ]
    post_flight_coords = [ (e['lat'], e['lon']) for e in events if datetime.fromisoformat(e['timestamp']) > arr_time ]

    if pre_flight_coords:
        folium.PolyLine(pre_flight_coords, color="#3498db", weight=5, popup="Pre-Flight Path").add_to(m)
    if post_flight_coords:
        folium.PolyLine(post_flight_coords, color="#3498db", weight=5, popup="Post-Flight Path").add_to(m)

    # Draw flight path between last and first ground points
    if pre_flight_coords and post_flight_coords:
        flight_path = [pre_flight_coords[-1], post_flight_coords[0]]
        folium.PolyLine(flight_path, color="#f39c12", weight=4, dash_array='10, 5', popup="Flight Path").add_to(m)
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
            reset_url = f"{BACKEND_URL}/reset_trip"
            response = requests.post(reset_url)
            response.raise_for_status()
            st.sidebar.success("Trip data has been reset!")
            st_autorefresh(interval=1, limit=2, key="reset_refresh") # A quick refresh to show the result
        except requests.exceptions.RequestException as e:
            st.sidebar.error(f"Error: {e}")
else:
    st.sidebar.info("Add `?a=neelaksh` to the URL for admin actions like resetting a trip.")
