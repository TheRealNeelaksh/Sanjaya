"""
Utility functions for Project Sanjaya v2.1
- Session hash generation
- Haversine distance calculation
- API usage tracking
"""
import hashlib
import json
import os
from datetime import datetime
from math import radians, sin, cos, sqrt, atan2
from typing import Optional


def generate_session_hash(username: str, timestamp: Optional[datetime] = None) -> str:
    """
    Generate a unique session hash for trip tracking links
    Format: SHA256(username + timestamp)
    
    Args:
        username: User's username
        timestamp: Optional timestamp (defaults to current time)
    
    Returns:
        64-character hexadecimal hash
    """
    if timestamp is None:
        timestamp = datetime.utcnow()
    
    data = f"{username}_{timestamp.isoformat()}".encode('utf-8')
    return hashlib.sha256(data).hexdigest()


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on Earth
    Uses the Haversine formula
    
    Args:
        lat1, lon1: Coordinates of first point
        lat2, lon2: Coordinates of second point
    
    Returns:
        Distance in meters
    """
    # Earth's radius in meters
    R = 6371000
    
    # Convert to radians
    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    delta_lat = radians(lat2 - lat1)
    delta_lon = radians(lon2 - lon1)
    
    # Haversine formula
    a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    
    distance = R * c
    return distance


def is_inside_geofence(lat: float, lon: float, geofence_lat: float, 
                       geofence_lon: float, radius_m: float) -> bool:
    """
    Check if a point is inside a circular geofence
    
    Args:
        lat, lon: Point coordinates
        geofence_lat, geofence_lon: Geofence center coordinates
        radius_m: Geofence radius in meters
    
    Returns:
        True if inside geofence, False otherwise
    """
    distance = haversine_distance(lat, lon, geofence_lat, geofence_lon)
    return distance <= radius_m


def get_current_place(lat: float, lon: float, geofences: list) -> str:
    """
    Determine current place name based on geofence matching
    
    Args:
        lat, lon: Current coordinates
        geofences: List of geofence objects with name, lat, lon, radius_m
    
    Returns:
        Place name if inside a geofence, "Travelling" otherwise
    """
    for geofence in geofences:
        if is_inside_geofence(lat, lon, geofence.lat, geofence.lon, geofence.radius_m):
            return geofence.name
    
    return "Travelling"


class APIUsageTracker:
    """
    Track API usage for AviationStack
    Maintains a JSON log file with call counts and timestamps
    """
    
    def __init__(self, log_file: str = "logs/api_usage.json"):
        self.log_file = log_file
        self._ensure_log_file()
    
    def _ensure_log_file(self):
        """Create log file if it doesn't exist"""
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w') as f:
                json.dump({"total_calls": 0, "calls": []}, f, indent=2)
    
    def log_api_call(self, endpoint: str, flight_number: str = None, 
                     response_status: str = "success") -> dict:
        """
        Log an API call
        
        Args:
            endpoint: API endpoint called
            flight_number: Flight number (if applicable)
            response_status: success or error
        
        Returns:
            Updated usage data
        """
        with open(self.log_file, 'r') as f:
            data = json.load(f)
        
        call_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "endpoint": endpoint,
            "flight_number": flight_number,
            "status": response_status
        }
        
        data["total_calls"] += 1
        data["calls"].append(call_record)
        
        with open(self.log_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        return data
    
    def get_usage_stats(self) -> dict:
        """
        Get current usage statistics
        
        Returns:
            Dictionary with total_calls and call history
        """
        with open(self.log_file, 'r') as f:
            return json.load(f)
    
    def get_monthly_calls(self, year: int = None, month: int = None) -> int:
        """
        Get number of calls made in a specific month
        
        Args:
            year: Year (defaults to current)
            month: Month (defaults to current)
        
        Returns:
            Number of API calls in that month
        """
        now = datetime.utcnow()
        year = year or now.year
        month = month or now.month
        
        with open(self.log_file, 'r') as f:
            data = json.load(f)
        
        count = 0
        for call in data["calls"]:
            call_time = datetime.fromisoformat(call["timestamp"])
            if call_time.year == year and call_time.month == month:
                count += 1
        
        return count
    
    def can_make_call(self, monthly_limit: int = 100) -> bool:
        """
        Check if we can make another API call within monthly limit
        
        Args:
            monthly_limit: Maximum calls per month
        
        Returns:
            True if under limit, False otherwise
        """
        monthly_calls = self.get_monthly_calls()
        return monthly_calls < monthly_limit
    
    def reset_monthly_stats(self):
        """Reset statistics (admin function)"""
        with open(self.log_file, 'w') as f:
            json.dump({"total_calls": 0, "calls": []}, f, indent=2)


def get_tracking_link(base_url: str, username: str, session_hash: str) -> str:
    """
    Generate a tracking link for a trip
    
    Args:
        base_url: NGROK base URL
        username: User's username
        session_hash: Unique session hash
    
    Returns:
        Full tracking URL
    """
    return f"{base_url}/track/{username}-{session_hash}"


def parse_tracking_id(tracking_id: str) -> tuple:
    """
    Parse tracking ID into username and session hash
    
    Args:
        tracking_id: Format "username-sessionhash"
    
    Returns:
        Tuple of (username, session_hash)
    """
    parts = tracking_id.split('-', 1)
    if len(parts) != 2:
        raise ValueError("Invalid tracking ID format")
    return parts[0], parts[1]