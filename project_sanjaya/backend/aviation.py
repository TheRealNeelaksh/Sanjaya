import requests
import os
from dotenv import load_dotenv
from . import utils
from apscheduler.schedulers.background import BackgroundScheduler
import datetime
from sqlalchemy.orm import Session

load_dotenv(dotenv_path="project_sanjaya/.env")
AVIATIONSTACK_KEY = os.getenv("AVIATIONSTACK_KEY")

API_BASE_URL = "http://api.aviationstack.com/v1/"

scheduler = BackgroundScheduler()
scheduler.start()

def get_flight_data(flight_iata: str):
    """Fetches flight data from AviationStack."""
    if not AVIATIONSTACK_KEY:
        raise ValueError("AVIATIONSTACK_KEY not set in .env file")

    usage = utils.increment_api_usage("aviationstack")
    if usage > 100:
        # TODO: Add more robust logging and fallback mechanism
        print("WARNING: AviationStack API usage is over 100 requests this month.")
        return None

    params = {
        "access_key": AVIATIONSTACK_KEY,
        "flight_iata": flight_iata,
    }
    response = requests.get(f"{API_BASE_URL}flights", params=params)
    return response.json()

def schedule_inflight_checks(db: Session, trip_id: int, flight_iata: str, dep_time: datetime, arr_time: datetime):
    """Schedules four in-flight checks for a given flight."""
    duration_minutes = (arr_time - dep_time).total_seconds() / 60
    interval = duration_minutes / 5  # 4 checks, so 5 intervals

    for i in range(1, 5):
        check_time = dep_time + datetime.timedelta(minutes=i * interval)
        scheduler.add_job(
            _update_flight_status,
            'date',
            run_date=check_time,
            args=[db, trip_id, flight_iata],
        )
    print(f"Scheduled 4 in-flight checks for trip {trip_id}")

def _update_flight_status(db: Session, trip_id: int, flight_iata: str):
    """Callback function to update the flight status."""
    print(f"Updating flight status for trip {trip_id}...")
    flight_data = get_flight_data(flight_iata)
    # TODO: Process and store the flight data
    print(flight_data)
