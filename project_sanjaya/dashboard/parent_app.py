import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
import os

API_URL = os.environ.get("API_URL", "http://127.0.0.1:8000")

def get_headers():
    return {"Authorization": f"Bearer {st.session_state.token}"}

def get_linked_children():
    response = requests.get(f"{API_URL}/linked-children", headers=get_headers())
    if response.status_code == 200:
        return [user['username'] for user in response.json()]
    return []

def get_child_status(username):
    response = requests.get(f"{API_URL}/child-status/{username}", headers=get_headers())
    if response.status_code == 200:
        return response.json()
    return None

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
    st.subheader(f"Welcome, {st.session_state.username}!")

    children = get_linked_children()
    selected_child = st.selectbox("Select a child to track:", children)

    if selected_child:
        child_status = get_child_status(selected_child)

        if child_status:
            col1, col2 = st.columns(2)
            with col1:
                if child_status["latitude"] and child_status["longitude"]:
                    display_map([{"lat": child_status["latitude"], "lon": child_status["longitude"]}])
                else:
                    st.warning("No location data available.")
            with col2:
                st.metric("Connection Status", child_status["connection_status"])
                st.metric("Last Seen", child_status["last_seen"])
                st.metric("Battery", f"{child_status['battery']}%" if child_status['battery'] else "N/A")
        else:
            st.error("Could not retrieve child status.")
