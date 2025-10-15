import os
import json
import sys
from datetime import datetime, timezone, timedelta
from flask import Flask, render_template, request, jsonify
import uuid

# Ensure the 'jules' module can be found
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from jules.utils import check_airport_proximity, haversine_distance
# aviation.py is no longer used

# --- Constants & Configuration ---
app = Flask(__name__, template_folder='templates')
TRIP_INFO_PATH = "/tmp/trip_info.json" # Vercel uses a /tmp directory for temporary file storage
TRIP_LOG_PATH = "/tmp/trip_log.json"

# --- Trip Management Endpoints ---

@app.route('/')
def index():
    """Serves the main tracking web page."""
    return render_template('index.html')

@app.route('/start_trip', methods=['POST'])
def start_trip():
    """Starts a trip with hardcoded flight details."""
    trip_info = {
        "trip_id": str(uuid.uuid4()),
        "user_name": "Neelaksh Saxena",
        "flight_number": "6E451",
        "trip_start_time": datetime.now(timezone.utc).isoformat(),
        "trip_status": "active",
        "flight_info": {
            "status": "scheduled",
            "scheduled_departure": "2025-10-16T16:15:00+00:00", # Hardcoded BLR-LKO schedule
            "scheduled_arrival": "2025-10-16T18:50:00+00:00"
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

@app.route('/update_status')
def update_status():
    """
    This endpoint is called by a Vercel Cron Job to update the trip status.
    """
    if not os.path.exists(TRIP_INFO_PATH):
        return "No active trip.", 200

    with open(TRIP_INFO_PATH, "r+") as f:
        trip_info = json.load(f)
        if trip_info.get("trip_status") != "active":
            return "Trip is not active.", 200

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
            return f"Status updated to: {new_status}", 200

    return "No status change.", 200