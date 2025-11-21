"""
Parent Dashboard for Project Sanjaya v2.1
Streamlit interface for parents to:
- View children's locations
- Track trips in real-time
- Receive alerts
"""
import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
from datetime import datetime
import time


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


# Initialize session state
if "token" not in st.session_state:
    st.session_state.token = None
if "user" not in st.session_state:
    st.session_state.user = None
if "auto_refresh" not in st.session_state:
    st.session_state.auto_refresh = True


# Main app
def main():
    st.set_page_config(
        page_title="Sanjaya - Parent Dashboard",
        page_icon="👨‍👩‍👧",
        layout="wide"
    )
    
    st.title("👨‍👩‍👧 Parent Dashboard - Project Sanjaya")
    
    # Authentication
    if not st.session_state.token:
        show_auth_page()
    else:
        show_dashboard()
        
        # Auto-refresh every 5 seconds if enabled
        if st.session_state.auto_refresh:
            time.sleep(5)
            st.rerun()


def show_auth_page():
    """Show login page"""
    st.subheader("Parent Login")
    
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if login(username, password):
            if st.session_state.user["role"] == "parent":
                st.success("Logged in successfully!")
                st.rerun()
            else:
                st.error("This dashboard is for parents only")
                st.session_state.token = None
                st.session_state.user = None
        else:
            st.error("Invalid credentials")


def show_dashboard():
    """Show main dashboard"""
    user = st.session_state.user
    token = st.session_state.token
    
    # Header
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        st.write(f"**Logged in as:** {user['username']}")
    
    with col2:
        auto_refresh = st.checkbox("Auto-refresh", value=st.session_state.auto_refresh)
        st.session_state.auto_refresh = auto_refresh
    
    with col3:
        if st.button("Logout"):
            st.session_state.token = None
            st.session_state.user = None
            st.rerun()
    
    st.divider()
    
    # Get children
    response = make_request("/my_children", auth_token=token)
    
    if response and response.status_code == 200:
        children = response.json()["children"]
        
        if not children:
            st.info("No children linked to your account")
            show_link_child_section(token)
        else:
            st.subheader("Your Children")
            
            for child in children:
                show_child_card(child, token)
    else:
        st.error("Failed to load children data")


def show_child_card(child, token):
    """Display a card for each child with their status"""
    with st.expander(f"👤 {child['username']}", expanded=child['has_active_trip']):
        if child['has_active_trip']:
            st.success("✅ Currently tracking")
            
            # Fetch tracking data
            tracking_link = child['tracking_link']
            response = make_request(tracking_link)
            
            if response and response.status_code == 200:
                data = response.json()
                trip = data['trip']
                locations = data['locations']
                
                # Trip info
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Status", trip['status'].capitalize())
                with col2:
                    st.metric("Mode", trip['mode'].capitalize())
                with col3:
                    st.metric("Current Place", trip['current_place'])
                
                # Map
                if locations:
                    st.subheader("Live Location")
                    show_map(locations)
                    
                    # Location history
                    with st.expander("Location History"):
                        for loc in reversed(locations[-10:]):  # Show last 10
                            st.write(f"🕐 {loc['timestamp'][:19]} - {loc['lat']:.4f}, {loc['lon']:.4f}")
                            if loc['battery']:
                                st.write(f"   🔋 Battery: {loc['battery']}%")
                else:
                    st.info("No location data yet")
            else:
                st.error("Failed to load tracking data")
        else:
            st.info("No active trip")


def show_map(locations):
    """Display map with location markers"""
    if not locations:
        return
    
    # Get last location for centering
    last_loc = locations[-1]
    center_lat = last_loc['lat']
    center_lon = last_loc['lon']
    
    # Create map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=13,
        tiles='OpenStreetMap'
    )
    
    # Add markers for all locations
    for i, loc in enumerate(locations):
        # Determine color (blue for path, red for current)
        color = 'red' if i == len(locations) - 1 else 'blue'
        
        folium.CircleMarker(
            location=[loc['lat'], loc['lon']],
            radius=5 if i == len(locations) - 1 else 3,
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.6,
            popup=f"Time: {loc['timestamp'][:19]}"
        ).add_to(m)
    
    # Draw polyline
    if len(locations) > 1:
        points = [[loc['lat'], loc['lon']] for loc in locations]
        folium.PolyLine(
            points,
            color='blue',
            weight=2,
            opacity=0.7
        ).add_to(m)
    
    # Display map
    st_folium(m, width=700, height=400)


def show_link_child_section(token):
    """Show section to link a child"""
    st.divider()
    st.subheader("Link a Child")
    
    col1, col2 = st.columns(2)
    
    with col1:
        parent_username = st.session_state.user['username']
        st.text_input("Your Username", value=parent_username, disabled=True)
    
    with col2:
        child_username = st.text_input("Child's Username")
    
    if st.button("Link Child"):
        if not child_username:
            st.error("Please enter child's username")
        else:
            response = make_request("/link_child", "POST", {
                "parent_username": parent_username,
                "child_username": child_username
            }, auth_token=token)
            
            if response and response.status_code == 200:
                st.success(f"Successfully linked to {child_username}")
                st.rerun()
            else:
                st.error("Failed to link child. Check if username exists and is a child account.")


if __name__ == "__main__":
    main()