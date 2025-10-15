import argparse
import sys
import os
import json
from datetime import datetime, timezone, timedelta
import time
import threading
from flask import Flask, render_template, request, jsonify
import uuid

# Ensure the 'jules' module can be found
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from jules.utils import check_airport_proximity, haversine_distance
from jules.aviation import get_flight_data
from jules.maps import generate_trip_map, capture_map_screenshot

# --- Constants & Configuration ---
app = Flask(__name__, template_folder='templates')
TRIP_INFO_PATH = "logs/trip_info.json"
TRIP_LOG_PATH = "logs/trip_log.json"

# --- Trip Management ---

@app.route('/start_trip', methods=['POST'])
def start_trip():
    data = request.get_json()
    if not data or 'name' not in data or 'flightNumber' not in data:
        return jsonify({"status": "error", "message": "Invalid data"}), 400

    # Immediately fetch flight schedule
    flight_iata = data['flightNumber']
    flight_schedule = get_flight_data(flight_iata)

    departure_info = flight_schedule.get('data', [{}])[0].get('departure', {})
    arrival_info = flight_schedule.get('data', [{}])[0].get('arrival', {})

    trip_info = {
        "trip_id": str(uuid.uuid4()),
        "user_name": data['name'],
        "flight_number": flight_iata,
        "pnr": data.get('pnr', 'N/A'),
        "trip_start_time": datetime.now(timezone.utc).isoformat(),
        "trip_status": "active",
        "current_tracking_status": "idle",
        "active_segment_id": None,
        "segments": [],
        "flight_info": {
            "status": "scheduled",
            "scheduled_departure": departure_info.get('scheduled'),
            "scheduled_arrival": arrival_info.get('scheduled')
        }
    }

    with open(TRIP_INFO_PATH, "w") as f:
        json.dump(trip_info, f, indent=2)

    with open(TRIP_LOG_PATH, "w") as f:
        json.dump({"events": []}, f, indent=2)

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
            log_data = json.load(f_log)
            log_data["events"].append(log_entry)
            f_log.seek(0); json.dump(log_data, f_log, indent=2)

        # --- Geofencing Logic ---
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
    with open(TRIP_INFO_PATH, "r+") as f:
        trip_info = json.load(f)
        trip_info["trip_status"] = "ended"
        trip_info["trip_end_time"] = datetime.now(timezone.utc).isoformat()
        f.seek(0); f.truncate(); json.dump(trip_info, f, indent=2)

    # --- Generate Final Map Image ---
    with open(TRIP_LOG_PATH, "r") as f:
        log_data = json.load(f)
        events = log_data.get("events", [])

    if events:
        html_path = generate_trip_map(events)
        if html_path:
            capture_map_screenshot(html_path)
            print("Final map image has been generated.")

    print(f"Trip ended: {trip_info['trip_id']}.")
    return jsonify(trip_info)

@app.route('/status')
def get_status():
    with open(TRIP_INFO_PATH, "r") as f:
        trip_info = json.load(f)
    return jsonify({
        "trip_status": trip_info.get("trip_status"),
        "current_tracking_status": trip_info.get("current_tracking_status"),
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

            # Only proceed if the trip is active and flight is in a trackable state
            if trip_info.get("trip_status") != "active" or flight_info.get("status") not in ["at_airport", "in_flight"]:
                time.sleep(30); continue

            # Check if we are within the flight window
            departure_time = datetime.fromisoformat(flight_info["scheduled_departure"]) if flight_info.get("scheduled_departure") else None
            arrival_time = datetime.fromisoformat(flight_info["scheduled_arrival"]) if flight_info.get("scheduled_arrival") else None

            # Only poll API if current time is between departure and arrival + buffer
            if departure_time and arrival_time and (departure_time - timedelta(minutes=30) < now_utc < arrival_time + timedelta(hours=2)):
                print(f"Checking flight status for {trip_info['flight_number']}...")
                flight_data = get_flight_data(trip_info['flight_number'])

                if flight_data and flight_data.get('data'):
                    details = flight_data['data'][0]
                    live = details.get('live')

                    # Update status and log coordinates
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

                time.sleep(60 * 25) # Poll every 25 minutes
            else:
                time.sleep(60) # Wait a minute if outside the flight window

# This file is now designed to be imported by `run_app.py`
# and no longer has a direct entry point.