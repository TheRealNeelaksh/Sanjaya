"""
Offline Sync Client for Project Sanjaya v2.1
- Caches location updates when offline
- Pushes them to the backend when online
- Uses cached_points.json
"""
import json
import os
import time
import requests
from datetime import datetime

CACHE_FILE = "logs/cached_points.json"
API_BASE_URL = "http://localhost:8000"  # Backend URL
SYNC_INTERVAL = 10  # seconds


def load_cache():
    """Load cached points from file"""
    if not os.path.exists(CACHE_FILE):
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        save_cache([])
        return []
    
    try:
        with open(CACHE_FILE, "r") as f:
            data = json.load(f)
            # Handle both old and new format
            if isinstance(data, list):
                return data
            return data.get("cached_locations", [])
    except Exception as e:
        print(f"[ERROR] Failed to load cache: {e}")
        return []


def save_cache(data):
    """Save cached points to file"""
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump({"cached_locations": data}, f, indent=2)
    except Exception as e:
        print(f"[ERROR] Failed to save cache: {e}")


def add_point(point):
    """Add a point to the cache"""
    cache = load_cache()
    cache.append(point)
    save_cache(cache)
    print(f"[CACHE] Saved point (Total cached: {len(cache)})")


def sync_cached_points(jwt_token):
    """
    Sync cached points to the backend
    Uses active trip from JWT token
    
    Args:
        jwt_token: JWT authentication token
    
    Returns:
        True if sync successful, False otherwise
    """
    cache = load_cache()
    
    if not cache:
        print("[INFO] No cached points to sync.")
        return True
    
    print(f"[SYNC] Attempting to sync {len(cache)} cached points...")
    
    headers = {"Authorization": f"Bearer {jwt_token}"}
    
    # Transform cache format to match API expectations
    locations = [
        {
            "lat": point["lat"],
            "lon": point["lon"],
            "battery": point.get("battery"),
            "timestamp": point["timestamp"]
        }
        for point in cache
    ]
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/sync_data",
            json={"locations": locations},
            headers=headers,
            timeout=10,
        )
        
        if response.status_code == 200:
            print(f"[SYNC] ✓ Successfully synced {len(locations)} points.")
            save_cache([])  # Clear cache after successful sync
            return True
        else:
            print(f"[SYNC ERROR] Server returned {response.status_code}: {response.text}")
            return False
    
    except requests.exceptions.RequestException as e:
        print(f"[SYNC] ✗ Server unreachable: {e.__class__.__name__}. Will retry later.")
        return False


def is_online(jwt_token):
    """
    Check if backend is reachable
    
    Args:
        jwt_token: JWT authentication token
    
    Returns:
        True if online, False otherwise
    """
    try:
        headers = {"Authorization": f"Bearer {jwt_token}"}
        response = requests.get(
            f"{API_BASE_URL}/health",
            headers=headers,
            timeout=3
        )
        return response.status_code == 200
    except:
        return False


def update_location(lat, lon, battery, jwt_token):
    """
    Update location - sends to server if online, caches if offline
    
    Args:
        lat: Latitude
        lon: Longitude
        battery: Battery percentage
        jwt_token: JWT authentication token
    
    Returns:
        Dictionary with result
    """
    point = {
        "lat": lat,
        "lon": lon,
        "battery": battery,
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    headers = {"Authorization": f"Bearer {jwt_token}"}
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/update_location",
            json=point,
            headers=headers,
            timeout=5,
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"[LIVE] ✓ Point uploaded: {lat:.4f}, {lon:.4f} → {result.get('current_place', 'Unknown')}")
            
            # Try to sync any cached points
            cached_count = len(load_cache())
            if cached_count > 0:
                print(f"[SYNC] Detected {cached_count} cached points, attempting sync...")
                sync_cached_points(jwt_token)
            
            return {"success": True, "method": "online"}
        else:
            print(f"[CACHE] Server rejected ({response.status_code}) → saving offline.")
            add_point(point)
            return {"success": True, "method": "cached"}
    
    except requests.exceptions.RequestException as e:
        print(f"[CACHE] No internet ({e.__class__.__name__}) → saving offline point.")
        add_point(point)
        return {"success": True, "method": "cached"}


def simulate_offline_tracking(jwt_token, interval=10):
    """
    Simulates location tracking with offline caching
    
    Args:
        jwt_token: JWT authentication token
        interval: Seconds between updates (default: 10)
    """
    print("\n" + "="*50)
    print("   OFFLINE TRACKING SIMULATOR")
    print("="*50)
    print(f"Update interval: {interval} seconds")
    print(f"Backend URL: {API_BASE_URL}")
    print(f"Cache file: {CACHE_FILE}")
    print("Press Ctrl+C to stop\n")
    
    # Starting coordinates (Delhi, India as example)
    base_lat = 28.6139
    base_lon = 77.2090
    
    iteration = 0
    
    try:
        while True:
            iteration += 1
            
            # Simulate movement (small random changes)
            lat = base_lat + (iteration * 0.001)  # Move north
            lon = base_lon + ((iteration % 10) * 0.0005)  # Slight east-west variation
            battery = max(10, 100 - (iteration % 90))  # Simulate battery drain
            
            print(f"\n[ITERATION {iteration}]")
            print(f"  Location: {lat:.6f}, {lon:.6f}")
            print(f"  Battery: {battery}%")
            
            # Update location
            result = update_location(lat, lon, battery, jwt_token)
            
            # Show cache status
            cached_count = len(load_cache())
            if cached_count > 0:
                print(f"  📦 Cache: {cached_count} points waiting to sync")
            
            time.sleep(interval)
    
    except KeyboardInterrupt:
        print("\n\n⏹️  Tracking stopped by user")
        cached_count = len(load_cache())
        if cached_count > 0:
            print(f"⚠️  Warning: {cached_count} points still in cache")
            print("💡 Run sync manually or they will upload on next connection")


def manual_sync(jwt_token):
    """
    Manually trigger sync of cached points
    
    Args:
        jwt_token: JWT authentication token
    """
    print("\n[MANUAL SYNC] Starting...")
    
    if not is_online(jwt_token):
        print("[ERROR] Backend is offline. Cannot sync.")
        return False
    
    cached_count = len(load_cache())
    
    if cached_count == 0:
        print("[INFO] No cached points to sync.")
        return True
    
    print(f"[INFO] Found {cached_count} cached points")
    result = sync_cached_points(jwt_token)
    
    if result:
        print("[SUCCESS] Sync completed successfully")
    else:
        print("[FAILED] Sync failed")
    
    return result


if __name__ == "__main__":
    import sys
    
    print("="*50)
    print("  Offline Sync Client for Project Sanjaya v2.1")
    print("="*50)
    
    if len(sys.argv) < 2:
        print("\nUsage:")
        print("  python sync_client.py <jwt_token> [--simulate] [--sync]")
        print("\nExamples:")
        print("  # Simulate tracking with offline caching")
        print("  python sync_client.py YOUR_JWT_TOKEN --simulate")
        print("")
        print("  # Manually sync cached points")
        print("  python sync_client.py YOUR_JWT_TOKEN --sync")
        print("")
        sys.exit(1)
    
    jwt_token = sys.argv[1]
    
    if "--simulate" in sys.argv:
        # Simulate tracking
        interval = 10
        if "--interval" in sys.argv:
            try:
                idx = sys.argv.index("--interval")
                interval = int(sys.argv[idx + 1])
            except:
                pass
        
        simulate_offline_tracking(jwt_token, interval)
    
    elif "--sync" in sys.argv:
        # Manual sync
        manual_sync(jwt_token)
    
    else:
        print("\n[INFO] No action specified. Use --simulate or --sync")
        print(f"[INFO] Cached points: {len(load_cache())}")
        print(f"[INFO] Backend online: {is_online(jwt_token)}")