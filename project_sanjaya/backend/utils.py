import hashlib
import os
import time
import secrets
import json
from math import radians, sin, cos, sqrt, atan2

def generate_session_hash(username: str) -> str:
    """Generates a secure session hash for a trip."""
    salt = secrets.token_hex(16)
    s = f"{username}{time.time()}{salt}"
    return hashlib.sha256(s.encode()).hexdigest()

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates the distance between two points on Earth in meters."""
    R = 6371000  # Earth radius in meters
    phi1, phi2 = radians(lat1), radians(lat2)
    dphi, dlambda = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dphi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(dlambda / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

def is_inside_geofence(lat: float, lon: float, geofence: dict) -> bool:
    """Checks if a coordinate is inside a geofence."""
    return haversine(lat, lon, geofence['lat'], geofence['lon']) <= geofence['radius_m']

def increment_api_usage(api_name: str = "aviationstack"):
    """Increments the usage count for a given API and logs it."""
    path = "project_sanjaya/logs/api_usage.json"
    data = {api_name: 0}
    if os.path.exists(path):
        with open(path, 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                pass  # Handle empty or corrupted file

    data[api_name] = data.get(api_name, 0) + 1

    with open(path, 'w') as f:
        json.dump(data, f)

    return data[api_name]

# TODO: Add unit tests for these functions.
