import argparse
import sys
import os
import json
from datetime import datetime, timezone
import time
import threading
from flask import Flask, render_template, request, jsonify

# Ensure the 'jules' module can be found
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from jules.tracker import start_tracking
from jules.utils import check_airport_proximity, haversine_distance
from jules.aviation import get_flight_data

# --- Background Flight Tracker ---
def flight_tracker_thread():
    """
    A background thread that monitors the session status and
    activates flight tracking when appropriate.
    """
    print("✈️  Flight tracker thread started.")
    while True:
        if not os.path.exists(SESSION_INFO_PATH):
            time.sleep(10)
            continue

        with open(SESSION_INFO_PATH, "r") as f:
            session_info = json.load(f)

        # Only track if the status is 'at_airport' or 'in_flight'
        if session_info.get("status") in ["at_airport", "in_flight"]:
            flight_iata = session_info.get("flight_number")
            if not flight_iata:
                time.sleep(10)
                continue

            print(f"Checking flight status for {flight_iata}...")
            flight_data = get_flight_data(flight_iata)

            if flight_data and flight_data.get('data'):
                flight_details = flight_data['data'][0] # Assuming first result is correct
                flight_status = flight_details.get('flight_status')

                # --- Update Session Status based on Flight Status ---
                if flight_status == 'active' and session_info.get("status") != 'in_flight':
                    print(f"Flight {flight_iata} is now active. Switching to in-flight tracking.")
                    session_info['status'] = 'in_flight'
                elif flight_status == 'landed' and session_info.get("status") != 'landed':
                    print(f"Flight {flight_iata} has landed.")
                    session_info['status'] = 'landed'

                # --- Log Flight Coordinates ---
                if flight_status == 'active' and flight_details.get('live'):
                    live_data = flight_details['live']
                    log_entry = {
                        "lat": live_data['latitude'],
                        "lon": live_data['longitude'],
                        "altitude": live_data.get('altitude'),
                        "speed": live_data.get('speed_horizontal'),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "source": "flight"
                    }
                    # Append to the main log file
                    with open(LOG_PATH, "r+") as f:
                        log_data = json.load(f)
                        log_data['events'].append(log_entry)
                        f.seek(0)
                        json.dump(log_data, f, indent=2)
                    print(f"Logged flight location: Lat {live_data['latitude']}, Lon {live_data['longitude']}")

                # Write updated session info back
                with open(SESSION_INFO_PATH, "w") as f:
                    json.dump(session_info, f, indent=2)

            # Wait for a longer interval to avoid spamming the API
            time.sleep(60 * 5) # Check every 5 minutes
        else:
            # If not in an airport/flight state, check less frequently
            time.sleep(30)

# --- Flask App ---
app = Flask(__name__, template_folder='templates')
LOG_PATH = "logs/session_log.json"
SESSION_INFO_PATH = "logs/session_info.json" # To store user details

@app.route('/')
def index():
    """Serves the main tracking web page."""
    return render_template('index.html')

@app.route('/start_session', methods=['POST'])
def start_session():
    """Receives user details and initializes a new session."""
    data = request.get_json()
    if not data or 'name' not in data or 'flightNumber' not in data:
        return jsonify({"status": "error", "message": "Invalid data"}), 400

    session_info = {
        "user_name": data['name'],
        "flight_number": data['flightNumber'],
        "pnr": data.get('pnr', 'N/A'),
        "start_time": datetime.now(timezone.utc).isoformat(),
        "status": "active"
    }

    # Store session info
    with open(SESSION_INFO_PATH, "w") as f:
        json.dump(session_info, f, indent=2)

    # Initialize or clear the session log for the new session
    with open(LOG_PATH, "w") as f:
        json.dump({"events": []}, f, indent=2)

    print(f"Session started for {data['name']} with flight {data['flightNumber']}")
    return jsonify({"status": "success"})

@app.route('/log', methods=['POST'])
def log_location():
    """Receives location data, logs it, and checks for airport proximity."""
    data = request.get_json()
    if not data or 'lat' not in data or 'lon' not in data:
        return jsonify({"status": "error", "message": "Invalid data"}), 400

    user_lat, user_lon = data['lat'], data['lon']

    log_entry = {
        "lat": user_lat,
        "lon": user_lon,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "web"
    }

    # Load existing location data and append
    session_data = {"events": []}
    if os.path.exists(LOG_PATH) and os.path.getsize(LOG_PATH) > 0:
        with open(LOG_PATH, "r") as f:
            try:
                session_data = json.load(f)
            except json.JSONDecodeError:
                pass

    session_data["events"].append(log_entry)

    with open(LOG_PATH, "w") as f:
        json.dump(session_data, f, indent=2)

    # --- Geofencing Logic ---
    session_info = {}
    if os.path.exists(SESSION_INFO_PATH):
        with open(SESSION_INFO_PATH, "r") as f:
            session_info = json.load(f)

    # Only check if the status is currently 'active' to prevent re-triggering
    if session_info.get('status') == 'active':
        nearby_airport = check_airport_proximity(user_lat, user_lon)
        if nearby_airport:
            session_info['status'] = 'at_airport'
            session_info['detected_airport'] = nearby_airport
            with open(SESSION_INFO_PATH, "w") as f:
                json.dump(session_info, f, indent=2)
            print(f"User entered geofence for {nearby_airport['name']}. Status updated.")

    print(f"Logged from web: Lat {user_lat}, Lon {user_lon}")
    return jsonify({"status": "success"})

@app.route('/session_status')
def session_status():
    """Provides the current session status to the frontend."""
    if not os.path.exists(SESSION_INFO_PATH):
        return jsonify({"status": "inactive"})

    with open(SESSION_INFO_PATH, "r") as f:
        session_info = json.load(f)

    return jsonify({"status": session_info.get("status", "unknown")})

@app.route('/stop_session', methods=['POST'])
def stop_session():
    """Marks the session as complete and generates a trip summary."""
    session_info = {}
    if os.path.exists(SESSION_INFO_PATH):
        with open(SESSION_INFO_PATH, "r") as f:
            session_info = json.load(f)

    session_info['status'] = 'stopped'
    end_time_iso = datetime.now(timezone.utc).isoformat()
    session_info['end_time'] = end_time_iso

    with open(SESSION_INFO_PATH, "w") as f:
        json.dump(session_info, f, indent=2)

    # --- Generate Trip Summary ---
    location_data = {"events": []}
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, "r") as f:
            location_data = json.load(f)

    events = location_data.get("events", [])
    total_distance_km = 0
    if len(events) > 1:
        for i in range(len(events) - 1):
            p1 = events[i]
            p2 = events[i+1]
            # Only calculate distance for ground points to avoid huge flight jumps
            if p1.get('source') != 'flight' and p2.get('source') != 'flight':
                total_distance_km += haversine_distance(p1['lat'], p1['lon'], p2['lat'], p2['lon'])

    start_time = datetime.fromisoformat(session_info.get('start_time').replace("Z", ""))
    end_time = datetime.fromisoformat(end_time_iso.replace("Z", ""))
    duration = end_time - start_time

    summary = {
        "user_name": session_info.get('user_name'),
        "flight_number": session_info.get('flight_number'),
        "start_time": session_info.get('start_time'),
        "end_time": end_time_iso,
        "duration_seconds": duration.total_seconds(),
        "total_ground_distance_km": round(total_distance_km, 2),
        "total_points_logged": len(events)
    }

    with open("logs/trip_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print("Session stopped and summary generated.")
    return jsonify(summary)

# --- Command-Line Interface ---
def main():
    parser = argparse.ArgumentParser(description="Project Sanjaya")
    parser.add_argument("command", choices=["start", "serve"], help="'start' for IP tracking, 'serve' for web UI.")
    args = parser.parse_args()

    if args.command == "start":
        print("🚀 Starting Jules IP Tracker...")
        start_tracking()
    elif args.command == "serve":
        print("🚀 Starting Jules Web Server...")
        print("🌍 Open the tracking link on your mobile device. Find the URL on your network below.")

        # Start the background thread for flight tracking
        tracker = threading.Thread(target=flight_tracker_thread, daemon=True)
        tracker.start()

        app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    main()