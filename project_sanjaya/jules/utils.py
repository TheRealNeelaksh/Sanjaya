import json
import os
from math import radians, sin, cos, sqrt, atan2

AIRPORTS_FILE = os.path.join(os.path.dirname(__file__), 'airports.json')

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate the distance between two points on Earth in kilometers."""
    R = 6371  # Radius of Earth in kilometers

    lat1_rad, lon1_rad = radians(lat1), radians(lon1)
    lat2_rad, lon2_rad = radians(lat2), radians(lon2)

    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad

    a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c

def check_airport_proximity(user_lat, user_lon):
    """
    Check if a user's location is within the geofence of any airport.
    Returns the airport information if a match is found, otherwise None.
    """
    if not os.path.exists(AIRPORTS_FILE):
        return None

    with open(AIRPORTS_FILE, 'r') as f:
        airports = json.load(f)

    for airport in airports:
        distance = haversine_distance(user_lat, user_lon, airport['lat'], airport['lon'])
        if distance <= airport['radius_km']:
            return airport

    return None

def get_airport_coords(iata_code):
    """Looks up an airport's coordinates by its IATA code."""
    if not os.path.exists(AIRPORTS_FILE):
        return None

    with open(AIRPORTS_FILE, 'r') as f:
        airports = json.load(f)

    for airport in airports:
        if airport['iata'] == iata_code:
            return (airport['lat'], airport['lon'])

    return None