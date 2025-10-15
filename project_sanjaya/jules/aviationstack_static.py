import requests
from dateutil import parser
from datetime import datetime, timezone
import os
import json

API_KEY = os.getenv("AVIATIONSTACK_KEY")
BASE_URL = 'http://api.aviationstack.com/v1/flights'

def get_flight_data(airline_iata=None, flight_iata=None, date=None):
    params = {'access_key': API_KEY}
    if airline_iata: params['airline_iata'] = airline_iata
    if flight_iata: params['flight_iata'] = flight_iata
    if date: params['departure_date'] = date

    try:
        response = requests.get(BASE_URL, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()

        if 'data' not in data or not data['data']:
            try:
                fallback_path = os.path.join(os.path.dirname(__file__), "fallback_flight.json")
                return json.load(open(fallback_path))
            except FileNotFoundError:
                return {"error": "No flight data found and fallback file missing."}

        flight = data['data'][0]
        def parse_time(t): return parser.parse(t) if t else None

        dep_sched_dt = parse_time(flight.get('departure', {}).get('scheduled'))
        arr_sched_dt = parse_time(flight.get('arrival', {}).get('scheduled'))

        flight_duration = None
        if dep_sched_dt and arr_sched_dt:
            delta = arr_sched_dt - dep_sched_dt
            hours, rem = divmod(delta.total_seconds(), 3600)
            minutes = rem // 60
            flight_duration = f"{int(hours)}h {int(minutes)}m"

        time_left = None
        if arr_sched_dt and arr_sched_dt > datetime.now(timezone.utc):
            delta = arr_sched_dt - datetime.now(timezone.utc)
            hours, rem = divmod(delta.total_seconds(), 3600)
            minutes = rem // 60
            time_left = f"{int(hours)}h {int(minutes)}m"

        return {
            "departure_airport": flight.get('departure', {}).get('airport', 'N/A'),
            "arrival_airport": flight.get('arrival', {}).get('airport', 'N/A'),
            "departure_scheduled": dep_sched_dt.isoformat() if dep_sched_dt else None,
            "arrival_scheduled": arr_sched_dt.isoformat() if arr_sched_dt else None,
            "status": flight.get('flight_status', 'N/A'),
            "flight_duration": flight_duration,
            "time_left_to_land": time_left
        }

    except requests.exceptions.RequestException as e:
        return {"error": f"API request failed: {e}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e}"}