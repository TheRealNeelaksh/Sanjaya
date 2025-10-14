import requests, os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

def get_flight_data(flight_iata):
    """
    Fetches flight data from AviationStack API.
    """
    key = os.getenv("AVIATIONSTACK_KEY")
    if not key or key == "YOUR_API_KEY_HERE":
        print("Error: AVIATIONSTACK_KEY not found or not set in .env file.")
        return None

    url = f"http://api.aviationstack.com/v1/flights"
    params = {
        'access_key': key,
        'flight_iata': flight_iata
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raises an exception for 4XX/5XX errors
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching flight data: {e}")
        return None