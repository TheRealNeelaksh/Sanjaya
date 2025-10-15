import requests
from dateutil import parser
from datetime import timezone, datetime
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))
BASE_URL = 'https://aerodatabox.p.rapidapi.com'

def get_flight_data(flight_number, flight_date):
    """
    Fetches and processes flight data from AeroDataBox API using the correct endpoint.
    flight_number is in the format: "6E451"
    flight_date is in the format: "2025-10-16"
    """
    api_key = os.getenv("RAPIDAPI_KEY")
    if not api_key:
        return {"error": "RAPIDAPI_KEY not found."}

    url = f"{BASE_URL}/flights/{flight_number}/{flight_date}"

    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": "aerodatabox.p.rapidapi.com"
    }

    try:
        response = requests.get(url, headers=headers, params={"withLocation": "true"}, timeout=20)
        response.raise_for_status()
        data = response.json()

        if not data or not isinstance(data, list) or not data[0]:
            return {"error": "No flight data found."}

        flight = data[0]

        def parse_time(t_str):
            return parser.parse(t_str) if t_str else None

        departure = flight.get('departure', {})
        arrival = flight.get('arrival', {})

        dep_sched_dt = parse_time(departure.get('scheduledTimeUtc'))
        arr_sched_dt = parse_time(arrival.get('scheduledTimeUtc'))

        flight_duration = None
        if dep_sched_dt and arr_sched_dt:
            duration_delta = arr_sched_dt - dep_sched_dt
            hours, rem = divmod(duration_delta.total_seconds(), 3600)
            minutes = rem // 60
            flight_duration = f"{int(hours)}h {int(minutes)}m"

        live_data = flight.get('location')
        time_left = None
        if arr_sched_dt and arr_sched_dt > datetime.now(timezone.utc):
            time_left_delta = arr_sched_dt - datetime.now(timezone.utc)
            hours, rem = divmod(time_left_delta.total_seconds(), 3600)
            minutes = rem // 60
            time_left = f"{int(hours)}h {int(minutes)}m"


        return {
            "departure_airport": departure.get('airport', {}).get('name', 'N/A'),
            "arrival_airport": arrival.get('airport', {}).get('name', 'N/A'),
            "departure_scheduled": dep_sched_dt.isoformat() if dep_sched_dt else None,
            "arrival_scheduled": arr_sched_dt.isoformat() if arr_sched_dt else None,
            "status": flight.get('status', 'N/A'),
            "live_data": live_data,
            "flight_duration": flight_duration,
            "time_left_to_land": time_left
        }

    except requests.exceptions.RequestException as e:
        return {"error": f"API request failed: {e}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e}"}