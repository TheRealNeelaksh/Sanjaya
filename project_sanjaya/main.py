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

@app.route('/airlines')
def get_airlines():
    """Provides the list of airlines to the frontend."""
    with open(os.path.join(os.path.dirname(__file__), 'jules', 'airlines.json')) as f:
        airlines = json.load(f)
    return jsonify(airlines)

@app.route('/start_trip', methods=['POST'])
def start_trip():
    """Instantly starts a trip and sets it to pending for the background thread."""
    data = request.get_json()
    required_fields = ['name', 'flightNumber', 'pnr', 'departureDate']
    if not data or not all(field in data for field in required_fields):
        return jsonify({"status": "error", "message": "Invalid data"}), 400

    flight_iata = data['flightNumber']

    trip_info = {
        "trip_id": str(uuid.uuid4()),
        "user_name": data['name'],
        "flight_number": flight_iata,
        "departure_date": data['departureDate'],
        "pnr": data.get('pnr', 'N/A'),
        "trip_start_time": datetime.now(timezone.utc).isoformat(),
        "trip_status": "active",
        "current_tracking_status": "idle",
        "active_segment_id": None,
        "segments": [],
        "flight_info": {
            "status": "pending_schedule", # New status for the background thread to pick up
            "scheduled_departure": None,
            "scheduled_arrival": None
        }
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
    if not os.path.exists(TRIP_INFO_PATH):
        return jsonify({"trip_status": "none"})
    with open(TRIP_INFO_PATH, "r") as f:
        trip_info = json.load(f)
    return jsonify({
        "trip_status": trip_info.get("trip_status"), "current_tracking_status": trip_info.get("current_tracking_status"),
        "flight_status": trip_info.get("flight_info", {}).get("status")
    })

@app.route('/reset_trip', methods=['POST'])
def reset_trip():
    """Deletes the current trip's log files."""
    if os.path.exists(TRIP_INFO_PATH):
        os.remove(TRIP_INFO_PATH)
    if os.path.exists(TRIP_LOG_PATH):
        os.remove(TRIP_LOG_PATH)
    print("Trip data has been reset.")
    return jsonify({"status": "success"})

# --- Smart Flight Tracker ---
def flight_tracker_thread():
    print("✈️  Smart flight tracker thread started.")
    while True:
        time.sleep(10) # Check every 10 seconds for new tasks
        if not os.path.exists(TRIP_INFO_PATH):
            continue

        with open(TRIP_INFO_PATH, "r+") as f:
            trip_info = json.load(f)
            if trip_info.get("trip_status") != "active":
                continue

            flight_info = trip_info.get("flight_info", {})
            flight_status = flight_info.get("status")

            # --- Task 1: Fetch Schedule for Pending Trips ---
            if flight_status == "pending_schedule":
                print(f"Fetching schedule for flight {trip_info['flight_number']}...")
                airline_iata = trip_info['flight_number'][:2]
                flight_schedule = get_flight_data(trip_info['flight_number'], trip_info['departure_date'], airline_iata)

                flight_data_list = flight_schedule.get('data', [])
                if flight_data_list:
                    departure_info = flight_data_list[0].get('departure', {})
                    arrival_info = flight_data_list[0].get('arrival', {})
                    flight_info["scheduled_departure"] = departure_info.get('scheduled')
                    flight_info["scheduled_arrival"] = arrival_info.get('scheduled')
                    flight_info["status"] = "scheduled"
                    print(f"✅ Schedule fetched for {trip_info['flight_number']}.")
                else:
                    print(f"⚠️  Could not fetch schedule for {trip_info['flight_number']}. Will retry.")
                    flight_info["status"] = "schedule_failed" # Mark as failed to avoid retrying too often

                trip_info['flight_info'] = flight_info
                f.seek(0); f.truncate(); json.dump(trip_info, f, indent=2)
                continue # Restart loop to re-read file

            # --- Task 2: Monitor Live Flight Status ---
            if flight_status in ["at_airport", "in_flight"]:
                now_utc = datetime.now(timezone.utc)
                departure_time = datetime.fromisoformat(flight_info["scheduled_departure"]) if flight_info.get("scheduled_departure") else None
                arrival_time = datetime.fromisoformat(flight_info["scheduled_arrival"]) if flight_info.get("scheduled_arrival") else None

                if departure_time and arrival_time and (departure_time - timedelta(minutes=30) < now_utc < arrival_time + timedelta(hours=2)):
                    print(f"Checking live status for {trip_info['flight_number']}...")
                    flight_data = get_flight_data(trip_info['flight_number'], trip_info['departure_date'])

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

                    time.sleep(60 * 25) # Wait 25 minutes for next check