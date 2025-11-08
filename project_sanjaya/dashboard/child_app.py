import streamlit as st
import requests
import json
import os
import time
from streamlit_folium import st_folium
import folium
import sys

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from dashboard import maps

API_URL = os.environ.get("API_URL", "http://127.0.0.1:8000")
CACHE_FILE = "project_sanjaya/logs/cached_points.json"

st.set_page_config(layout="wide")

def login_user(username, password):
    response = requests.post(f"{API_URL}/login", json={"username": username, "password": password})
    if response.status_code == 200:
        st.session_state.token = response.json()["access_token"]
        st.session_state.username = username
        return True
    return False

def get_headers():
    return {"Authorization": f"Bearer {st.session_state.token}"}

def start_trip(mode, details={}):
    response = requests.post(
        f"{API_URL}/start_trip",
        headers=get_headers(),
        json={"username": st.session_state.username, "mode": mode, "details": details}
    )
    if response.status_code == 200:
        st.session_state.session_hash = response.json()["session_hash"]
        return True
    return False

def update_location(lat, lon, battery):
    if "session_hash" not in st.session_state:
        st.error("Trip not started.")
        return

    data = {
        "session_hash": st.session_state.session_hash,
        "lat": lat,
        "lon": lon,
        "battery": battery,
    }
    try:
        response = requests.post(f"{API_URL}/update_location", headers=get_headers(), json=data)
        if response.status_code == 200:
            st.success("Location updated.")
            sync_cached_points()
        else:
            cache_point(data)
            st.warning("Offline. Caching location.")
    except requests.exceptions.ConnectionError:
        cache_point(data)
        st.warning("Offline. Caching location.")

def cache_point(data):
    points = []
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            points = json.load(f)
    points.append(data)
    with open(CACHE_FILE, 'w') as f:
        json.dump(points, f)

def sync_cached_points():
    if not os.path.exists(CACHE_FILE):
        return

    with open(CACHE_FILE, 'r') as f:
        points = json.load(f)

    if not points:
        return

    try:
        response = requests.post(f"{API_URL}/sync_data", headers=get_headers(), json={"session_hash": st.session_state.session_hash, "points": points})
        if response.status_code == 200:
            os.remove(CACHE_FILE)
            st.success("Synced cached points.")
    except requests.exceptions.ConnectionError:
        pass # Will retry on next update

def geofence_editor():
    st.subheader("Geofence Editor")
    lat, lon = maps.geofence_map()
    if lat and lon:
        st.write(f"Selected coordinates: {lat:.6f}, {lon:.6f}")
        name = st.text_input("Geofence Name")
        radius = st.number_input("Radius (meters)", min_value=50, max_value=1000, value=100)
        if st.button("Save Geofence"):
            # TODO: Implement API call to save geofence
            st.success(f"Geofence '{name}' saved.")

def main():
    st.title("Child Dashboard")

    if 'token' not in st.session_state:
        st.subheader("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if login_user(username, password):
                st.rerun()
            else:
                st.error("Invalid credentials.")
    else:
        st.subheader(f"Welcome, {st.session_state.username}!")

        if st.button("Logout"):
            del st.session_state.token
            st.rerun()

        geofence_editor()

        st.subheader("Start Tracking")
        if st.button("Start College Tracking"):
            if start_trip("college"):
                st.success("College tracking started.")
            else:
                st.error("Failed to start college tracking.")

        with st.expander("Start Trip Tracking"):
            trip_type = st.selectbox("Trip Type", ["Flight", "Train", "Road"])
            if trip_type == "Flight":
                flight_iata = st.text_input("Flight IATA Number")
                if st.button("Start Flight Trip"):
                    if start_trip("flight", {"flight_iata": flight_iata}):
                        st.success("Flight trip started.")
                    else:
                        st.error("Failed to start flight trip.")
            # TODO: Add forms for Train and Road trips

        if "session_hash" in st.session_state:
            st.subheader("Live Tracking")
            st.write(f"Session Hash: {st.session_state.session_hash}")

            # TODO: Implement browser API integration for live location and battery data.
            st.warning("Live location and battery data are not yet implemented in the browser.")

            # Send heartbeat
            if "last_heartbeat" not in st.session_state or time.time() - st.session_state.last_heartbeat > 30:
                requests.post(f"{API_URL}/heartbeat", headers=get_headers())
                st.session_state.last_heartbeat = time.time()

            # This is a placeholder for real location data
            update_location(34.0522, -118.2437, 80.0)

if __name__ == "__main__":
    main()
