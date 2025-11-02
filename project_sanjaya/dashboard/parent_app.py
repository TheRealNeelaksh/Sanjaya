import streamlit as st
import requests
import folium
from streamlit_folium import st_folium

API_URL = "http://127.0.0.1:8000"

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

def get_linked_children():
    response = requests.get(f"{API_URL}/linked-children", headers=get_headers())
    if response.status_code == 200:
        return [user['username'] for user in response.json()]
    return []

def get_live_trip_data(username):
    # TODO: Implement API endpoint to get live trip data
    # For now, returning mock data
    return {
        "locations": [
            {"lat": 34.0522, "lon": -118.2437},
            {"lat": 34.0622, "lon": -118.2537},
            {"lat": 34.0722, "lon": -118.2637},
        ],
        "status": "Travelling",
        "last_update": "2024-10-16 10:30:00",
        "battery": "75%",
    }

def display_map(locations):
    if not locations:
        st.warning("No location data available.")
        return

    map_center = [locations[-1]["lat"], locations[-1]["lon"]]
    m = folium.Map(location=map_center, zoom_start=14)

    folium.PolyLine(locations=[(loc["lat"], loc["lon"]) for loc in locations]).add_to(m)
    folium.Marker(location=map_center, popup="Current Location").add_to(m)

    st_folium(m, width=700, height=500)

def main():
    st.title("Parent Dashboard")

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

        children = get_linked_children()
        selected_child = st.selectbox("Select a child to track:", children)

        if selected_child:
            trip_data = get_live_trip_data(selected_child)

            col1, col2 = st.columns(2)
            with col1:
                display_map(trip_data["locations"])
            with col2:
                st.metric("Status", trip_data["status"])
                st.metric("Last Update", trip_data["last_update"])
                st.metric("Battery", trip_data["battery"])

if __name__ == "__main__":
    main()
