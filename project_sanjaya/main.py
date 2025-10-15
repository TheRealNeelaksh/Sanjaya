import os
import json
import sys
import time
from datetime import datetime, timezone, timedelta
from flask import Flask, render_template, request, jsonify
import uuid

# Ensure the 'jules' module can be found
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from jules.utils import check_airport_proximity, haversine_distance
# aviation.py is no longer used

# --- Constants & Configuration ---
app = Flask(__name__, template_folder='templates')
TRIP_INFO_PATH = "logs/trip_info.json"
TRIP_LOG_PATH = "logs/trip_log.json"

# --- Trip Management Endpoints ---

@app.route('/')
def index():
    """Serves the main tracking web page."""
    return render_template('index.html')

@app.route('/start_trip', methods=['POST'])
def start_trip():
    """Starts a trip with manually provided flight times."""
    data = request.get_json()
    required_fields = ['name', 'departure_time', 'arrival_time']
    if not data or not all(field in data for field in required_fields):
        return jsonify({"status": "error", "message": "Invalid data"}), 400

    trip_info = {
        "trip_id": str(uuid.uuid4()),
        "user_name": data['name'],
        "trip_start_time": datetime.now(timezone.utc).isoformat(),
        "trip_status": "active",
        "flight_info": {
            "status": "scheduled",
            "scheduled_departure": data['departure_time'],
            "scheduled_arrival": data['arrival_time']
        }
    }

    with open(TRIP_INFO_PATH, "w") as f: json.dump(trip_info, f, indent=2)
    with open(TRIP_LOG_PATH, "w") as f: json.dump({"events": []}, f, indent=2)

    print(f"Trip started for {trip_info['user_name']}.")
    return jsonify(trip_info)

@app.route('/log', methods=['POST'])
def log_location():
    data = request.get_json()
    with open(TRIP_INFO_PATH, "r+") as f_info:
        trip_info = json.load(f_info)
        log_entry = { "lat": data['lat'], "lon": data['lon'], "timestamp": datetime.now(timezone.utc).isoformat(), "source": "web" }
        with open(TRIP_LOG_PATH, "r+") as f_log:
            log_data = json.load(f_log)
            log_data["events"].append(log_entry)
            f_log.seek(0); json.dump(log_data, f_log, indent=2)
    return jsonify({"status": "success"})

@app.route('/end_trip', methods=['POST'])
def end_trip():
    with open(TRIP_INFO_PATH, "r+") as f:
        trip_info = json.load(f)
        trip_info["trip_status"] = "ended"
        trip_info["trip_end_time"] = datetime.now(timezone.utc).isoformat()
        f.seek(0); f.truncate(); json.dump(trip_info, f, indent=2)
    return jsonify(trip_info)

@app.route('/status')
def get_status():
    if not os.path.exists(TRIP_INFO_PATH):
        return jsonify({"trip_status": "none"})
    with open(TRIP_INFO_PATH, "r") as f:
        trip_info = json.load(f)
    return jsonify({
        "trip_status": trip_info.get("trip_status"),
        "flight_status": trip_info.get("flight_info", {}).get("status")
    })

@app.route('/reset_trip', methods=['POST'])
def reset_trip():
    if os.path.exists(TRIP_INFO_PATH):
        os.remove(TRIP_INFO_PATH)
    if os.path.exists(TRIP_LOG_PATH):
        os.remove(TRIP_LOG_PATH)
    print("Trip data has been reset.")
    return jsonify({"status": "success"})

# --- Time-Based Status Updater ---
def time_based_status_thread():
    print("⏰ Time-based status updater thread started.")
    while True:
        time.sleep(60) # Check every minute
        if not os.path.exists(TRIP_INFO_PATH):
            continue

        with open(TRIP_INFO_PATH, "r+") as f:
            trip_info = json.load(f)
            if trip_info.get("trip_status") != "active":
                continue

            flight_info = trip_info.get("flight_info", {})
            now = datetime.now(timezone.utc)

            dep_time = datetime.fromisoformat(flight_info['scheduled_departure'])
            arr_time = datetime.fromisoformat(flight_info['scheduled_arrival'])
            boarding_time = dep_time - timedelta(minutes=45)

            new_status = flight_info['status']
            if boarding_time <= now < dep_time:
                new_status = 'boarding'
            elif dep_time <= now < arr_time:
                new_status = 'in_flight'
            elif now >= arr_time:
                new_status = 'landed'

            if new_status != flight_info['status']:
                flight_info['status'] = new_status
                trip_info['flight_info'] = flight_info
                f.seek(0); f.truncate(); json.dump(trip_info, f, indent=2)
                print(f"Status updated to: {new_status}")