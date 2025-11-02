import requests
import json
import time
import os

API_URL = "http://127.0.0.1:8000"
CACHE_FILE = "project_sanjaya/logs/cached_points_client.json"

def get_headers(token):
    return {"Authorization": f"Bearer {token}"}

def login(username, password):
    try:
        response = requests.post(f"{API_URL}/login", json={"username": username, "password": password})
        if response.status_code == 200:
            return response.json()["access_token"]
    except requests.exceptions.ConnectionError:
        return None
    return None

def update_location(token, session_hash, lat, lon, battery):
    data = {"session_hash": session_hash, "lat": lat, "lon": lon, "battery": battery}
    try:
        response = requests.post(f"{API_URL}/update_location", headers=get_headers(token), json=data)
        if response.status_code == 200:
            print("Location updated successfully.")
            return True
    except requests.exceptions.ConnectionError:
        pass

    print("Failed to update location. Caching...")
    points = []
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            points = json.load(f)
    points.append(data)
    with open(CACHE_FILE, 'w') as f:
        json.dump(points, f)
    return False

def sync_data(token, session_hash):
    if not os.path.exists(CACHE_FILE):
        return

    with open(CACHE_FILE, 'r') as f:
        points = json.load(f)

    if not points:
        return

    try:
        response = requests.post(f"{API_URL}/sync_data", headers=get_headers(token), json={"session_hash": session_hash, "points": points})
        if response.status_code == 200:
            print("Successfully synced cached data.")
            os.remove(CACHE_FILE)
    except requests.exceptions.ConnectionError:
        print("Failed to sync data. Will retry later.")


if __name__ == '__main__':
    # This is a simple simulation
    # In a real client, you would get these values from the UI or other inputs
    TEST_USERNAME = "testchild"
    TEST_PASSWORD = "password"

    # First, register the user if they don't exist
    try:
        requests.post(f"{API_URL}/register", json={"username": TEST_USERNAME, "password": TEST_PASSWORD, "role": "child"})
    except requests.exceptions.ConnectionError:
        print("Backend not running. Please start the backend server first.")
        exit()

    token = login(TEST_USERNAME, TEST_PASSWORD)
    if not token:
        print("Login failed. Please check credentials or backend server.")
        exit()

    # Start a trip to get a session hash
    response = requests.post(f"{API_URL}/start_trip", headers=get_headers(token), json={"username": TEST_USERNAME, "mode": "road"})
    session_hash = response.json()["session_hash"]

    lat, lon = 34.0, -118.0
    while True:
        sync_data(token, session_hash)
        update_location(token, session_hash, lat, lon, 90.0)
        lat += 0.01
        lon += 0.01
        time.sleep(10)
