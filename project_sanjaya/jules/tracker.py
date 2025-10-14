import geocoder, time, json, os
from datetime import datetime

LOG_PATH = "logs/session_log.json"

def get_location():
    g = geocoder.ip('me')
    return {"lat": g.latlng[0], "lon": g.latlng[1]}

def start_tracking(interval=300):
    # Adjust the log path to be relative to the project root
    log_file_path = os.path.join(os.path.dirname(__file__), '..', LOG_PATH)

    # Create logs directory if it doesn't exist
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

    session_data = {"events": []}
    # Load existing data if the file is not empty
    if os.path.exists(log_file_path) and os.path.getsize(log_file_path) > 0:
        try:
            with open(log_file_path, "r") as f:
                session_data = json.load(f)
        except json.JSONDecodeError:
            # Handle case where file is corrupt or empty
            session_data = {"events": []}

    while True:
        try:
            loc = get_location()
            if loc and loc.get("lat") is not None:
                loc["timestamp"] = datetime.utcnow().isoformat() + "Z"
                session_data["events"].append(loc)

                with open(log_file_path, "w") as f:
                    json.dump(session_data, f, indent=2)

                print(f"Logged: {loc}")
            else:
                print("Failed to fetch location.")

        except Exception as e:
            print(f"An error occurred: {e}")

        time.sleep(interval)