import streamlit as st
from streamlit_folium import st_folium
import folium

def geofence_map(center=[20, 0], zoom=2):
    """Creates an interactive map for geofence creation."""
    m = folium.Map(location=center, zoom_start=zoom)
    m.add_child(folium.LatLngPopup())

    map_data = st_folium(m, width=700, height=500)

    selected_lat = None
    selected_lon = None

    if map_data and map_data["last_clicked"]:
        selected_lat = map_data["last_clicked"]["lat"]
        selected_lon = map_data["last_clicked"]["lng"]

    return selected_lat, selected_lon
