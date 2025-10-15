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
from jules.aviation import get_flight_data

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
    data = request.get_json()
    if not data or 'name' not in data or 'flightNumber' not in data:
        return jsonify({"status": "error", "message": "Invalid data"}), 400

    flight_iata = data['flightNumber']
    flight_schedule = get_flight_data(flight_iata)

    departure_info = {}
    arrival_info = {}
    flight_data_list = flight_schedule.get('data', [])
    if flight_data_list:
        departure_info = flight_data_list[0].get('departure', {})
        arrival_info = flight_data_list[0].get('arrival', {})
    else:
        print(f"⚠️  Warning: Could not find flight data for {flight_iata}. Proceeding without flight schedule.")

    trip_info = {
        "trip_id": str(uuid.uuid4()), "user_name": data['name'], "flight_number": flight_iata,
        "pnr": data.get('pnr', 'N/A'), "trip_start_time": datetime.now(timezone.utc).isoformat(),
        "trip_status": "active", "current_tracking_status": "idle", "active_segment_id": None,
        "segments": [], "flight_info": { "status": "scheduled", "scheduled_departure": departure_info.get('scheduled'), "scheduled_arrival": arrival_info.get('scheduled') }
    }

    with open(TRIP_INFO_PATH, "w") as f: json.dump(trip_info, f, indent=2)
    with open(TRIP_LOG_PATH, "w") as f: json.dump({"events": []}, f, indent=2)

    print(f"Trip started for {trip_info['user_name']}. Flight schedule fetched.")
    return jsonify(trip_info)

@app.route('/start_segment', methods=['POST'])
def start_segment():
    with open(TRIP_INFO_PATH, "r+") as f:
        trip_info = json.load(f)
        new_segment = { "segment_id": str(uuid.uuid4()), "start_time": datetime.now(timezone.utc).isoformat(), "end_time": None, "status": "active" }
        trip_info["segments"].append(new_segment)
        trip_info["active_segment_id"] = new_segment["segment_id"]
        trip_info["current_tracking_status"] = "tracking"
        f.seek(0); f.truncate(); json.dump(trip_info, f, indent=2)
    return jsonify(trip_info)

@app.route('/stop_segment', methods=['POST'])
def stop_segment():
    with open(TRIP_INFO_PATH, "r+") as f:
        trip_info = json.load(f)
        active_segment_id = trip_info["active_segment_id"]
        for segment in trip_info["segments"]:
            if segment["segment_id"] == active_segment_id:
                segment["end_time"] = datetime.now(timezone.utc).isoformat(); segment["status"] = "stopped"; break
        trip_info["active_segment_id"] = None; trip_info["current_tracking_status"] = "idle"
        f.seek(0); f.truncate(); json.dump(trip_info, f, indent=2)
    return jsonify(trip_info)

@app.route('/log', methods=['POST'])
def log_location():
    data = request.get_json()
    with open(TRIP_INFO_PATH, "r+") as f_info:
        trip_info = json.load(f_info)
        active_segment_id = trip_info.get("active_segment_id")
        if not active_segment_id: return jsonify({"status": "error"}), 400

        log_entry = { "lat": data['lat'], "lon": data['lon'], "timestamp": datetime.now(timezone.utc).isoformat(), "source": "web", "segment_id": active_segment_id }

        with open(TRIP_LOG_PATH, "r+") as f_log:
            log_data = json.load(f_log); log_data["events"].append(log_entry)
            f_log.seek(0); json.dump(log_data, f_log, indent=2)

        if trip_info.get("flight_info", {}).get("status") == "scheduled":
            nearby_airport = check_airport_proximity(data['lat'], data['lon'])
            if nearby_airport:
                trip_info["flight_info"]["status"] = "at_airport"
                trip_info["flight_info"]["detected_airport"] = nearby_airport
                f_info.seek(0); f_info.truncate(); json.dump(trip_info, f_info, indent=2)
                print(f"User entered geofence for {nearby_airport['name']}.")

    return jsonify({"status": "success"})

@app.route('/end_trip', methods=['POST'])
def end_trip():
    # Implementation of map generation will be added in the next step
    with open(TRIP_INFO_PATH, "r+") as f:
        trip_info = json.load(f)
        trip_info["trip_status"] = "ended"; trip_info["trip_end_time"] = datetime.now(timezone.utc).isoformat()
        f.seek(0); f.truncate(); json.dump(trip_info, f, indent=2)
    return jsonify(trip_info)

@app.route('/status')
def get_status():
    with open(TRIP_INFO_PATH, "r") as f:
        trip_info = json.load(f)
    return jsonify({
        "trip_status": trip_info.get("trip_status"), "current_tracking_status": trip_info.get("current_tracking_status"),
        "flight_status": trip_info.get("flight_info", {}).get("status")
    })

# --- Smart Flight Tracker ---
def flight_tracker_thread():
    print("✈️  Smart flight tracker thread started.")
    while True:
        if not os.path.exists(TRIP_INFO_PATH):
            time.sleep(10); continue

        with open(TRIP_INFO_PATH, "r+") as f:
            trip_info = json.load(f)
            flight_info = trip_info.get("flight_info", {})
            now_utc = datetime.now(timezone.utc)

            if trip_info.get("trip_status") != "active" or flight_info.get("status") not in ["at_airport", "in_flight"]:
                time.sleep(30); continue

            departure_time = datetime.fromisoformat(flight_info["scheduled_departure"]) if flight_info.get("scheduled_departure") else None
            arrival_time = datetime.fromisoformat(flight_info["scheduled_arrival"]) if flight_info.get("scheduled_arrival") else None

            if departure_time and arrival_time and (departure_time - timedelta(minutes=30) < now_utc < arrival_time + timedelta(hours=2)):
                print(f"Checking flight status for {trip_info['flight_number']}...")
                flight_data = get_flight_data(trip_info['flight_number'])

                if flight_data and flight_data.get('data'):
                    details = flight_data['data'][0]
                    live = details.get('live')

                    if details.get('flight_status') == 'active':
                        flight_info['status'] = 'in_flight'
                        if live:
                            log_entry = { "lat": live['latitude'], "lon": live['longitude'], "timestamp": datetime.now(timezone.utc).isoformat(), "source": "flight" }
                            with open(TRIP_LOG_PATH, "r+") as f_log:
                                log_data = json.load(f_log); log_data["events"].append(log_entry)
                                f_log.seek(0); json.dump(log_data, f_log, indent=2)
                    elif details.get('flight_status') == 'landed':
                        flight_info['status'] = 'landed'

                    trip_info['flight_info'] = flight_info
                    f.seek(0); f.truncate(); json.dump(trip_info, f, indent=2)

                time.sleep(60 * 25)
            else:
                time.sleep(60)
import sys