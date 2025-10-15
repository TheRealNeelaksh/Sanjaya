import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

def get_flight_data(flight_number, departure_date=None, airline_iata=None):
    """
    Fetches flight data from AviationStack API using more specific parameters.
    """
    key = os.getenv("AVIATIONSTACK_KEY")
    if not key or key == "YOUR_API_KEY_HERE":
        print("Error: AVIATIONSTACK_KEY not found or not set in .env file.")
        return {} # Return empty dict on error

    url = f"http://api.aviationstack.com/v1/flights"

    params = {
        'access_key': key,
        'flight_number': flight_number
    }

    # Add optional parameters for a more specific search
    if airline_iata:
        params['airline_iata'] = airline_iata
    if departure_date:
        params['flight_date'] = departure_date

    try:
        response = requests.get(url, params=params, timeout=15) # 15-second timeout
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching flight data: {e}")
        return {} # Return empty dict on error