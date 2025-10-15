import os
from serpapi import GoogleSearch
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

def get_flight_data(flight_id, dep_iata, arr_iata, date):
    """
    Fetches flight data from SerpApi's Google Flights API.
    flight_id is in the format: "6E245"
    date is in the format: "2025-10-15"
    """
    api_key = os.getenv("SERPAPI_KEY")
    if not api_key:
        print("Error: SERPAPI_KEY not found in .env file.")
        return {}

    params = {
        "api_key": api_key,
        "engine": "google_flights",
        "flight_id": f"{flight_id}-{dep_iata}-{arr_iata}-{date}",
        "hl": "en"
    }

    try:
        search = GoogleSearch(params)
        results = search.get_dict()

        # Check for errors in the response
        if "error" in results:
            print(f"SerpApi Error: {results['error']}")
            return {}

        return results

    except Exception as e:
        print(f"An exception occurred while fetching flight data: {e}")
        return {}