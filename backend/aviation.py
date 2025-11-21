"""
AviationStack Integration for Project Sanjaya v2.1
Flight tracking with strict API budget control
Maximum ~4 API calls per flight
"""
import requests
import os
from datetime import datetime, timedelta
from typing import Optional, Dict
from apscheduler.schedulers.background import BackgroundScheduler
from utils import APIUsageTracker


class FlightTracker:
    """
    Flight tracking using AviationStack API
    Implements budget-aware polling (4 checks per flight)
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("AVIATIONSTACK_API_KEY")
        self.base_url = "http://api.aviationstack.com/v1/flights"
        self.usage_tracker = APIUsageTracker()
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        
        # Monthly API call limit
        self.MONTHLY_LIMIT = 100
        
    def _can_make_call(self) -> bool:
        """Check if we can make another API call"""
        return self.usage_tracker.can_make_call(self.MONTHLY_LIMIT)
    
    def fetch_flight_data(self, flight_number: str, flight_date: Optional[str] = None) -> Optional[Dict]:
        """
        Fetch flight data from AviationStack
        
        Args:
            flight_number: Flight number (e.g., "AA100")
            flight_date: Optional date in YYYY-MM-DD format
        
        Returns:
            Flight data dictionary or None if failed
        """
        if not self._can_make_call():
            print(f"⚠️ Monthly API limit reached ({self.MONTHLY_LIMIT} calls)")
            return None
        
        if not self.api_key:
            print("⚠️ AviationStack API key not configured")
            return None
        
        params = {
            "access_key": self.api_key,
            "flight_iata": flight_number
        }
        
        if flight_date:
            params["flight_date"] = flight_date
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            
            # Log API call
            status = "success" if response.status_code == 200 else "error"
            self.usage_tracker.log_api_call(
                endpoint="flights",
                flight_number=flight_number,
                response_status=status
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("data") and len(data["data"]) > 0:
                    return data["data"][0]  # Return first result
                else:
                    print(f"No data found for flight {flight_number}")
                    return None
            else:
                print(f"API Error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            self.usage_tracker.log_api_call(
                endpoint="flights",
                flight_number=flight_number,
                response_status="error"
            )
            return None
    
    def get_flight_status(self, flight_data: Dict) -> str:
        """
        Extract human-readable flight status
        
        Args:
            flight_data: Flight data from API
        
        Returns:
            Status string (e.g., "In Flight", "Landed", "Scheduled")
        """
        if not flight_data:
            return "Unknown"
        
        flight_status = flight_data.get("flight_status", "").lower()
        
        status_map = {
            "scheduled": "Scheduled",
            "active": "In Flight",
            "landed": "Landed",
            "cancelled": "Cancelled",
            "incident": "Incident",
            "diverted": "Diverted"
        }
        
        return status_map.get(flight_status, "Unknown")
    
    def get_flight_coordinates(self, flight_data: Dict) -> Optional[tuple]:
        """
        Extract current flight coordinates if available
        
        Args:
            flight_data: Flight data from API
        
        Returns:
            Tuple of (lat, lon) or None
        """
        if not flight_data:
            return None
        
        live = flight_data.get("live")
        if live:
            lat = live.get("latitude")
            lon = live.get("longitude")
            
            if lat is not None and lon is not None:
                return (float(lat), float(lon))
        
        return None
    
    def schedule_flight_checks(self, flight_number: str, departure_time: datetime, 
                               arrival_time: datetime, callback):
        """
        Schedule 4 strategic API checks during flight
        
        Args:
            flight_number: Flight number
            departure_time: Scheduled departure time
            arrival_time: Scheduled arrival time
            callback: Function to call with flight data
        
        Checks:
        1. Pre-takeoff (5 min before departure)
        2. Mid-flight (halfway through)
        3. Descent (15 min before landing)
        4. Post-landing (5 min after arrival)
        """
        now = datetime.utcnow()
        flight_duration = arrival_time - departure_time
        
        # Calculate check times
        check_times = []
        
        # Check 1: Pre-takeoff (5 min before)
        pre_takeoff = departure_time - timedelta(minutes=5)
        if pre_takeoff > now:
            check_times.append(("Pre-Takeoff", pre_takeoff))
        
        # Check 2: Mid-flight
        mid_flight = departure_time + (flight_duration / 2)
        if mid_flight > now:
            check_times.append(("Mid-Flight", mid_flight))
        
        # Check 3: Descent (15 min before landing)
        descent = arrival_time - timedelta(minutes=15)
        if descent > now:
            check_times.append(("Descent", descent))
        
        # Check 4: Post-landing (5 min after)
        post_landing = arrival_time + timedelta(minutes=5)
        if post_landing > now:
            check_times.append(("Post-Landing", post_landing))
        
        # Schedule all checks
        for check_name, check_time in check_times:
            if not self._can_make_call():
                print(f"⚠️ Cannot schedule {check_name} - API limit reached")
                continue
            
            self.scheduler.add_job(
                func=self._scheduled_check,
                trigger='date',
                run_date=check_time,
                args=[flight_number, check_name, callback],
                id=f"{flight_number}_{check_name}",
                replace_existing=True
            )
            
            print(f"✓ Scheduled {check_name} check for {flight_number} at {check_time}")
    
    def _scheduled_check(self, flight_number: str, check_name: str, callback):
        """
        Internal method for scheduled flight checks
        
        Args:
            flight_number: Flight number
            check_name: Name of the check
            callback: Function to call with results
        """
        print(f"🛫 Running {check_name} check for {flight_number}")
        
        flight_data = self.fetch_flight_data(flight_number)
        
        if flight_data:
            status = self.get_flight_status(flight_data)
            coords = self.get_flight_coordinates(flight_data)
            
            result = {
                "flight_number": flight_number,
                "check_name": check_name,
                "status": status,
                "coordinates": coords,
                "timestamp": datetime.utcnow(),
                "raw_data": flight_data
            }
            
            callback(result)
        else:
            print(f"⚠️ Failed to fetch data for {flight_number} during {check_name}")
    
    def get_usage_stats(self) -> Dict:
        """Get API usage statistics"""
        stats = self.usage_tracker.get_usage_stats()
        monthly_calls = self.usage_tracker.get_monthly_calls()
        
        return {
            "total_calls": stats["total_calls"],
            "monthly_calls": monthly_calls,
            "monthly_limit": self.MONTHLY_LIMIT,
            "remaining": self.MONTHLY_LIMIT - monthly_calls,
            "can_make_call": self._can_make_call()
        }
    
    def stop_scheduler(self):
        """Stop the background scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()


# Example callback function for flight updates
def flight_update_callback(flight_result: Dict):
    """
    Example callback for processing flight updates
    This should be customized to update database and send alerts
    
    Args:
        flight_result: Dictionary with flight status and coordinates
    """
    print(f"\n📊 Flight Update Received:")
    print(f"   Flight: {flight_result['flight_number']}")
    print(f"   Check: {flight_result['check_name']}")
    print(f"   Status: {flight_result['status']}")
    
    if flight_result['coordinates']:
        lat, lon = flight_result['coordinates']
        print(f"   Location: {lat:.4f}, {lon:.4f}")
    
    print(f"   Time: {flight_result['timestamp']}")
    
    # TODO: Update database with new location
    # TODO: Send alerts to parents if status changed
    # TODO: Update trip status in database


# Usage example
if __name__ == "__main__":
    # Initialize tracker
    tracker = FlightTracker()
    
    # Check usage
    stats = tracker.get_usage_stats()
    print(f"API Usage: {stats['monthly_calls']}/{stats['monthly_limit']}")
    
    # Fetch flight data
    flight_data = tracker.fetch_flight_data("AA100")
    
    if flight_data:
        print(f"Status: {tracker.get_flight_status(flight_data)}")
        coords = tracker.get_flight_coordinates(flight_data)
        if coords:
            print(f"Coordinates: {coords}")
    
    # Schedule checks (example)
    # departure = datetime.utcnow() + timedelta(hours=1)
    # arrival = departure + timedelta(hours=3)
    # tracker.schedule_flight_checks("AA100", departure, arrival, flight_update_callback)