import requests
from dateutil import parser
from datetime import timezone

def get_flight_data(api_key, airline_iata, flight_number, flight_date):
    """
    Fetches and processes flight data from AviationStack.
    Returns a dictionary with structured flight information.
    """
    params = {
        'access_key': api_key,
        'airline_iata': airline_iata,
        'flight_number': flight_number,
        'flight_date': flight_date,
        'limit': 1 # We only want the most relevant flight
    }

    try:
        response = requests.get('http://api.aviationstack.com/v1/flights', params=params, timeout=20)
        response.raise_for_status()
        data = response.json()

        if 'data' not in data or not data['data']:
            return {"error": "No flight data found."}

        flight = data['data'][0]

        # Helper to parse time strings safely
        def parse_time(t):
            return parser.parse(t) if t else None

        dep_sched_dt = parse_time(flight.get('departure', {}).get('scheduled'))
        arr_sched_dt = parse_time(flight.get('arrival', {}).get('scheduled'))
        dep_actual_dt = parse_time(flight.get('departure', {}).get('actual'))
        arr_estimated_dt = parse_time(flight.get('arrival', {}).get('estimated'))
        now = datetime.now(timezone.utc)

        flight_duration = None
        if dep_actual_dt and arr_estimated_dt:
            duration_delta = arr_estimated_dt - dep_actual_dt
            hours, rem = divmod(duration_delta.total_seconds(), 3600)
            minutes = rem // 60
            flight_duration = f"{int(hours)}h {int(minutes)}m"

        time_left = None
        if arr_estimated_dt and arr_estimated_dt > now:
            time_left_delta = arr_estimated_dt - now
            hours, rem = divmod(time_left_delta.total_seconds(), 3600)
            minutes = rem // 60
            time_left = f"{int(hours)}h {int(minutes)}m"

        return {
            "departure_airport": flight.get('departure', {}).get('airport', 'N/A'),
            "arrival_airport": flight.get('arrival', {}).get('airport', 'N/A'),
            "departure_scheduled": dep_sched_dt.isoformat() if dep_sched_dt else None,
            "arrival_scheduled": arr_sched_dt.isoformat() if arr_sched_dt else None,
            "status": flight.get('flight_status', 'N/A'),
            "live_data": flight.get('live'),
            "flight_duration": flight_duration,
            "time_left_to_land": time_left
        }

    except requests.exceptions.RequestException as e:
        return {"error": f"API request failed: {e}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e}"}