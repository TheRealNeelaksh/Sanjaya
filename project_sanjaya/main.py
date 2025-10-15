import os
import json
import sys
import time
import re
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
        "flight_number": data['flightNumber'],
        "departure_date": data['departureDate'],
        "dep_iata": data['depIATA'],
        "arr_iata": data['arrIATA'],
        "pnr": data.get('pnr', 'N/A'),
        "trip_start_time": datetime.now(timezone.utc).isoformat(),
        "trip_status": "active",
        "current_tracking_status": "idle",
        "active_segment_id": None,
        "segments": [],
        "flight_info": {
            "status": "pending_schedule",
            "scheduled_departure": None,
            "scheduled_arrival": None
        }
    }

    with open(TRIP_INFO_PATH, "w") as f: json.dump(trip_info, f, indent=2)
    with open(TRIP_LOG_PATH, "w") as f: json.dump({"events": []}, f, indent=2)

    print(f"Trip started for {trip_info['user_name']}. Flight schedule fetched.")
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

@app.route('/sync_flight', methods=['POST'])
def sync_flight():
    """Forces a manual sync of flight data."""
    if not os.path.exists(TRIP_INFO_PATH):
        return jsonify({"status": "error", "message": "No active trip"}), 404

    with open(TRIP_INFO_PATH, "r+") as f:
        trip_info = json.load(f)

        print(f"Manual sync requested for flight {trip_info['flight_number']}...")
        flight_data = get_flight_data(
            flight_id=trip_info['flight_number'],
            dep_iata=trip_info['dep_iata'],
            arr_iata=trip_info['arr_iata'],
            date=trip_info['departure_date']
        )

        if flight_data and "flight_info" in flight_data:
            flight_info_data = flight_data["flight_info"]
            airplane_tracker = flight_data.get("airplane_tracker", {})

            flight_info = trip_info.get("flight_info", {})
            flight_info["status"] = flight_info_data.get("status", "scheduled").lower()
            flight_info["live_data"] = airplane_tracker.get("live")

            departure_info = flight_info_data.get("departure_airport", {})
            arrival_info = flight_info_data.get("arrival_airport", {})
            flight_info["scheduled_departure"] = departure_info.get("time")
            flight_info["scheduled_arrival"] = arrival_info.get("time")

            trip_info['flight_info'] = flight_info
            f.seek(0); f.truncate(); json.dump(trip_info, f, indent=2)

            print(f"✅ Manual sync successful for {trip_info['flight_number']}.")
            return jsonify({"status": "success", "flight_info": flight_info})
        else:
            print(f"⚠️  Manual sync failed for {trip_info['flight_number']}.")
            return jsonify({"status": "error", "message": "Could not retrieve flight data."}), 500

from geopy.geocoders import Nominatim

# --- "Reached Home" Detector ---
def reached_home_thread():
    """
    A background thread that checks if the user has been stationary in a
    new state for over 30 minutes, and updates the status to 'home'.
    """
    geolocator = Nominatim(user_agent="jules_tracker")
    print("🏠 Reached home detector thread started.")
    while True:
        time.sleep(60 * 5) # Check every 5 minutes
        if not os.path.exists(TRIP_INFO_PATH) or not os.path.exists(TRIP_LOG_PATH):
            continue

        with open(TRIP_INFO_PATH, "r+") as f:
            trip_info = json.load(f)
            if trip_info.get("trip_status") != "active":
                continue

            with open(TRIP_LOG_PATH, "r") as f_log:
                log_data = json.load(f_log)
                events = log_data.get("events", [])

            if len(events) < 2:
                continue

            # Check for stationary period
            last_event_time = datetime.fromisoformat(events[-1]['timestamp'])
            if (datetime.now(timezone.utc) - last_event_time) > timedelta(minutes=30):

                # Get start and end locations
                start_location = geolocator.reverse(f"{events[0]['lat']}, {events[0]['lon']}", language='en')
                end_location = geolocator.reverse(f"{events[-1]['lat']}, {events[-1]['lon']}", language='en')

                if start_location and end_location:
                    start_state = start_location.raw.get('address', {}).get('state')
                    end_state = end_location.raw.get('address', {}).get('state')

                    if start_state and end_state and start_state != end_state:
                        print(f"✅ User detected as 'home' in new state: {end_state}")
                        trip_info['trip_status'] = 'home'
                        f.seek(0); f.truncate(); json.dump(trip_info, f, indent=2)

# --- Smart Flight Tracker ---
def flight_tracker_thread():
    """Background thread to fetch and update flight status using AeroDataBox."""
    print("✈️  Flight tracker thread started.")
    while True:
        time.sleep(15) # Check for work every 15 seconds
        if not os.path.exists(TRIP_INFO_PATH):
            continue

        with open(TRIP_INFO_PATH, "r+") as f:
            trip_info = json.load(f)

            if trip_info.get("trip_status") != "active" or trip_info.get("flight_info", {}).get("status") == "landed":
                continue

            print(f"Updating flight data for {trip_info['flight_number']}...")

            flight_data = get_flight_data(
                flight_number=trip_info['flight_number'],
                flight_date=trip_info['departure_date']
            )

            if "error" not in flight_data:
                trip_info['flight_info'] = flight_data

                live_data = flight_data.get('live_data')
                if live_data and live_data.get('latitude'):
                    log_entry = {
                        "lat": live_data['latitude'], "lon": live_data['longitude'],
                        "timestamp": datetime.now(timezone.utc).isoformat(), "source": "flight"
                    }
                    with open(TRIP_LOG_PATH, "r+") as f_log:
                        log_data = json.load(f_log)
                        log_data["events"].append(log_entry)
                        f_log.seek(0); f_log.truncate(); json.dump(log_data, f_log, indent=2)

                f.seek(0); f.truncate(); json.dump(trip_info, f, indent=2)
                print(f"✅ Flight data updated for {trip_info['flight_number']}.")
            else:
                print(f"⚠️  {flight_data['error']}")
                trip_info['flight_info']['status'] = 'failed'
                f.seek(0); f.truncate(); json.dump(trip_info, f, indent=2)

        time.sleep(60 * 10)