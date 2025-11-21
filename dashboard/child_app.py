"""
Child Dashboard for Project Sanjaya v2.1
Streamlit interface for children to:
- Start/stop tracking
- Define geofences
- View trip history
"""
import streamlit as st
import requests
from datetime import datetime
import json


# Configuration
API_BASE_URL = st.secrets.get("API_BASE_URL", "http://localhost:8000")


# Helper functions
def make_request(endpoint, method="GET", data=None, auth_token=None):
    """Make API request with error handling"""
    headers = {}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    url = f"{API_BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            headers["Content-Type"] = "application/json"
            response = requests.post(url, json=data, headers=headers)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        
        return response
    except Exception as e:
        st.error(f"Request failed: {e}")
        return None


def login(username, password):
    """Login and store token"""
    response = make_request("/login", "POST", {"username": username, "password": password})
    
    if response and response.status_code == 200:
        data = response.json()
        st.session_state.token = data["access_token"]
        st.session_state.user = data["user"]
        return True
    else:
        return False


def register(username, password):
    """Register new user"""
    response = make_request("/register", "POST", {
        "username": username,
        "password": password,
        "role": "child"
    })
    
    return response and response.status_code == 201


# Initialize session state
if "token" not in st.session_state:
    st.session_state.token = None
if "user" not in st.session_state:
    st.session_state.user = None


# Main app
def main():
    st.set_page_config(
        page_title="Sanjaya - Child Dashboard",
        page_icon="🧒",
        layout="wide"
    )
    
    st.title("🧒 Child Dashboard - Project Sanjaya")
    
    # Authentication
    if not st.session_state.token:
        show_auth_page()
    else:
        show_dashboard()


def show_auth_page():
    """Show login/register page"""
    st.subheader("Welcome to Project Sanjaya")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.subheader("Login")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login"):
            if login(username, password):
                st.success("Logged in successfully!")
                st.rerun()
            else:
                st.error("Invalid credentials")
    
    with tab2:
        st.subheader("Register")
        new_username = st.text_input("Username", key="register_username")
        new_password = st.text_input("Password", type="password", key="register_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
        
        if st.button("Register"):
            if new_password != confirm_password:
                st.error("Passwords do not match")
            elif len(new_password) < 6:
                st.error("Password must be at least 6 characters")
            elif register(new_username, new_password):
                st.success("Registration successful! Please login.")
            else:
                st.error("Registration failed. Username may already exist.")


def show_dashboard():
    """Show main dashboard"""
    user = st.session_state.user
    token = st.session_state.token
    
    st.write(f"**Logged in as:** {user['username']}")
    
    if st.button("Logout"):
        st.session_state.token = None
        st.session_state.user = None
        st.rerun()
    
    st.divider()
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["🗺️ Geofences", "🚗 Tracking", "📜 Trip History"])
    
    with tab1:
        show_geofences_tab(token)
    
    with tab2:
        show_tracking_tab(token)
    
    with tab3:
        show_history_tab(token)


def show_geofences_tab(token):
    """Geofence management tab"""
    st.subheader("Manage Geofences")
    st.write("Define your safe zones: Home, College, or custom places")
    
    # Fetch existing geofences
    response = make_request("/geofences", auth_token=token)
    
    if response and response.status_code == 200:
        geofences = response.json()["geofences"]
        
        if geofences:
            st.write("**Your Geofences:**")
            for gf in geofences:
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    st.write(f"**{gf['name']}**")
                with col2:
                    st.write(f"📍 {gf['lat']:.4f}, {gf['lon']:.4f}")
                with col3:
                    if st.button("Delete", key=f"delete_{gf['id']}"):
                        del_response = make_request(f"/geofences/{gf['id']}", "DELETE", auth_token=token)
                        if del_response and del_response.status_code == 200:
                            st.success("Deleted!")
                            st.rerun()
        else:
            st.info("No geofences defined yet")
    
    st.divider()
    
    # Add new geofence
    st.subheader("Add New Geofence")
    
    col1, col2 = st.columns(2)
    
    with col1:
        name = st.text_input("Place Name", placeholder="Home, College, Mall, etc.")
        lat = st.number_input("Latitude", format="%.6f", value=0.0)
        lon = st.number_input("Longitude", format="%.6f", value=0.0)
    
    with col2:
        radius = st.number_input("Radius (meters)", min_value=10, value=100)
        st.write("")
        st.write("")
        
        if st.button("Add Geofence"):
            if not name:
                st.error("Please enter a name")
            else:
                response = make_request("/geofences", "POST", {
                    "name": name,
                    "lat": lat,
                    "lon": lon,
                    "radius_m": radius
                }, auth_token=token)
                
                if response and response.status_code == 201:
                    st.success(f"Geofence '{name}' created!")
                    st.rerun()
                else:
                    st.error("Failed to create geofence")


def show_tracking_tab(token):
    """Trip tracking tab"""
    st.subheader("Start Tracking")
    
    # Check for active trip
    response = make_request("/my_trips", auth_token=token)
    active_trip = None
    
    if response and response.status_code == 200:
        trips = response.json()["trips"]
        for trip in trips:
            if trip["status"] == "active":
                active_trip = trip
                break
    
    if active_trip:
        st.success("✅ You have an active trip!")
        st.write(f"**Mode:** {active_trip['mode']}")
        st.write(f"**Started:** {active_trip['start_time']}")
        
        if st.button("End Trip", type="primary"):
            end_response = make_request("/end_trip", "POST", auth_token=token)
            if end_response and end_response.status_code == 200:
                st.success("Trip ended!")
                st.rerun()
    else:
        st.info("No active trip. Start tracking below.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            mode = st.selectbox(
                "Tracking Mode",
                ["college", "flight", "train", "road"],
                format_func=lambda x: x.capitalize()
            )
            
            start_place = st.text_input("Starting Place", placeholder="Optional")
            end_place = st.text_input("Destination", placeholder="Optional")
        
        with col2:
            st.write("**Trip Details (Optional)**")
            
            if mode == "flight":
                flight_number = st.text_input("Flight Number", placeholder="e.g., AA100")
                details = {"flight_number": flight_number} if flight_number else None
            elif mode == "train":
                train_number = st.text_input("Train Number", placeholder="e.g., 12345")
                details = {"train_number": train_number} if train_number else None
            else:
                details = None
        
        if st.button("Start Trip", type="primary"):
            trip_data = {
                "mode": mode,
                "start_place": start_place if start_place else None,
                "end_place": end_place if end_place else None,
                "details": details
            }
            
            response = make_request("/start_trip", "POST", trip_data, auth_token=token)
            
            if response and response.status_code == 201:
                result = response.json()
                st.success("Trip started!")
                st.write(f"**Tracking Link:** `{result['trip']['tracking_link']}`")
                st.rerun()
            else:
                st.error("Failed to start trip")


def show_history_tab(token):
    """Trip history tab"""
    st.subheader("Trip History")
    
    response = make_request("/my_trips", auth_token=token)
    
    if response and response.status_code == 200:
        trips = response.json()["trips"]
        
        if trips:
            for trip in trips:
                with st.expander(f"{trip['mode'].capitalize()} - {trip['start_time'][:10]}"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write(f"**Status:** {trip['status']}")
                    with col2:
                        st.write(f"**Mode:** {trip['mode']}")
                    with col3:
                        if trip['end_time']:
                            st.write(f"**Duration:** {trip['end_time'][:10]}")
        else:
            st.info("No trips yet")
    else:
        st.error("Failed to load trip history")


if __name__ == "__main__":
    main()