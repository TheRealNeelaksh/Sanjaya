"""
Master Launcher for Project Sanjaya v2.1
- Starts NGROK
- Starts FastAPI backend
- Starts Streamlit dashboards (child/parent/admin)
- Runs health checks
- Prints all URLs and system status
"""

import subprocess
import time
import requests
import os
import sys
from pyngrok import ngrok
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

FASTAPI_PORT = 8000
STREAMLIT_CHILD_PORT = 8501
STREAMLIT_PARENT_PORT = 8502
STREAMLIT_ADMIN_PORT = 8503


def start_backend():
    """Start FastAPI backend"""
    print("[START] Launching FastAPI backend...")
    return subprocess.Popen(
        ["uvicorn", "backend.app:app", "--reload", "--port", str(FASTAPI_PORT)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )


def start_streamlit(app, port):
    """Start Streamlit dashboard"""
    print(f"[START] Launching Streamlit: {app} on port {port}...")
    return subprocess.Popen(
        ["streamlit", "run", app, "--server.port", str(port), "--server.address", "localhost"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )


def start_ngrok():
    """Start NGROK tunnel"""
    print("[START] Starting NGROK tunnel...")
    
    # Get auth token from environment
    auth_token = os.getenv("NGROK_AUTH_TOKEN")
    
    if not auth_token:
        print("[WARNING] NGROK_AUTH_TOKEN not found in .env file")
        print("[INFO] Using localhost URL instead. Set NGROK_AUTH_TOKEN for remote access.")
        return f"http://localhost:{FASTAPI_PORT}"
    
    try:
        ngrok.set_auth_token(auth_token)
        public_url = ngrok.connect(FASTAPI_PORT).public_url
        print(f"[NGROK] ✓ Public URL: {public_url}")
        
        # Save to config file
        os.makedirs("logs", exist_ok=True)
        with open("logs/ngrok_config.json", "w") as f:
            import json
            json.dump({"ngrok_url": public_url, "timestamp": time.time()}, f, indent=2)
        
        return public_url
    except Exception as e:
        print(f"[FAIL] NGROK failed: {e}")
        print("[INFO] Continuing with localhost URL. Install NGROK or check auth token.")
        return f"http://localhost:{FASTAPI_PORT}"


def test_backend(base_url):
    """Test backend health"""
    print("[CHECK] Testing backend health...")
    max_retries = 10
    
    for i in range(max_retries):
        try:
            r = requests.get(base_url + "/health", timeout=3)
            if r.status_code == 200:
                print("[OK] ✓ Backend is healthy.")
                return True
            else:
                print(f"[RETRY] Backend returned {r.status_code}, retrying...")
        except Exception as e:
            print(f"[RETRY] Attempt {i+1}/{max_retries} - Backend not ready yet...")
        
        time.sleep(2)
    
    print("[FAIL] Backend health check failed after retries.")
    return False


def create_default_admin():
    """Create default admin account if it doesn't exist"""
    print("[SETUP] Checking for default admin account...")
    
    try:
        response = requests.post(
            f"http://localhost:{FASTAPI_PORT}/register",
            json={
                "username": "admin",
                "password": "admin123",
                "role": "admin"
            },
            timeout=5
        )
        
        if response.status_code == 201:
            print("[SETUP] ✓ Default admin account created")
            print("[INFO] Username: admin | Password: admin123")
            print("[WARNING] Change this password in production!")
            return True
        elif response.status_code == 400:
            print("[INFO] Admin account already exists")
            return True
        else:
            print(f"[WARNING] Could not create admin account: {response.text}")
            return False
    except Exception as e:
        print(f"[WARNING] Could not create admin account: {e}")
        return False


def get_admin_token():
    """Get JWT token for admin user"""
    try:
        response = requests.post(
            f"http://localhost:{FASTAPI_PORT}/login",
            json={
                "username": "admin",
                "password": "admin123"
            },
            timeout=5
        )
        
        if response.status_code == 200:
            token = response.json()["access_token"]
            return token
        else:
            return None
    except Exception as e:
        print(f"[WARNING] Could not get admin token: {e}")
        return None


def print_system_status(base_url, token=None):
    """Print system status with all data"""
    print("\n" + "="*50)
    print("     PROJECT SANJAYA v2.1 - SYSTEM STATUS")
    print("="*50)
    
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    # Users
    print("\n[USERS]")
    try:
        r = requests.get(base_url + "/admin/users", headers=headers, timeout=5)
        if r.status_code == 200:
            users = r.json()["users"]
            print(f"  Total Users: {len(users)}")
            for user in users:
                print(f"    - {user['username']} ({user['role']})")
        else:
            print(f"  Could not fetch users (Status: {r.status_code})")
    except Exception as e:
        print(f"  Could not fetch users: {e}")
    
    # Trips
    print("\n[TRIPS]")
    try:
        r = requests.get(base_url + "/admin/trips", headers=headers, timeout=5)
        if r.status_code == 200:
            trips = r.json()["trips"]
            active_trips = [t for t in trips if t["status"] == "active"]
            print(f"  Total Trips: {len(trips)}")
            print(f"  Active Trips: {len(active_trips)}")
            
            if active_trips:
                print("  Active:")
                for trip in active_trips[:5]:  # Show first 5
                    print(f"    - {trip['username']}: {trip['mode']} ({trip['status']})")
        else:
            print(f"  Could not fetch trips (Status: {r.status_code})")
    except Exception as e:
        print(f"  Could not fetch trips: {e}")
    
    # Geofences
    print("\n[GEOFENCES]")
    try:
        r = requests.get(base_url + "/admin/geofences", headers=headers, timeout=5)
        if r.status_code == 200:
            geofences = r.json()["geofences"]
            print(f"  Total Geofences: {len(geofences)}")
            for gf in geofences[:5]:  # Show first 5
                print(f"    - {gf['user']}: {gf['name']} ({gf['radius_m']}m)")
        else:
            print(f"  Could not fetch geofences (Status: {r.status_code})")
    except Exception as e:
        print(f"  Could not fetch geofences: {e}")
    
    # API usage
    print("\n[AVIATIONSTACK API USAGE]")
    try:
        if os.path.exists("logs/api_usage.json"):
            import json
            with open("logs/api_usage.json") as f:
                data = json.load(f)
                total = data.get("total_calls", 0)
                
                # Calculate monthly calls
                from datetime import datetime
                now = datetime.utcnow()
                monthly_calls = sum(
                    1 for call in data.get("calls", [])
                    if datetime.fromisoformat(call['timestamp']).month == now.month
                )
                
                print(f"  Total Calls: {total}")
                print(f"  This Month: {monthly_calls}/100")
                print(f"  Remaining: {100 - monthly_calls}")
        else:
            print("  No API usage data yet")
    except Exception as e:
        print(f"  Could not read API usage: {e}")
    
    print("\n" + "="*50 + "\n")


def print_access_urls(public_url):
    """Print all access URLs"""
    print("\n" + "="*50)
    print("           ACCESS LINKS")
    print("="*50)
    print(f"\n🌐 Backend API:")
    print(f"   Public:  {public_url}")
    print(f"   Local:   http://localhost:{FASTAPI_PORT}")
    print(f"   Docs:    {public_url}/docs")
    print(f"\n📱 Dashboards:")
    print(f"   Child:   http://localhost:{STREAMLIT_CHILD_PORT}")
    print(f"   Parent:  http://localhost:{STREAMLIT_PARENT_PORT}")
    print(f"   Admin:   http://localhost:{STREAMLIT_ADMIN_PORT}")
    print(f"\n🔗 Tracking:")
    print(f"   Pattern: {public_url}/track/<username>-<session_hash>")
    print(f"   Example: {public_url}/track/john-abc123...")
    print("\n" + "="*50 + "\n")


def cleanup_processes(processes):
    """Cleanup all processes on exit"""
    print("\n[CLEANUP] Stopping all services...")
    
    for name, process in processes.items():
        try:
            process.terminate()
            print(f"[CLEANUP] ✓ Stopped {name}")
        except Exception as e:
            print(f"[CLEANUP] ✗ Failed to stop {name}: {e}")
    
    # Stop NGROK
    try:
        ngrok.kill()
        print("[CLEANUP] ✓ Stopped NGROK")
    except:
        pass
    
    print("[CLEANUP] All services stopped.")


def main():
    """Main launcher function"""
    print("\n" + "="*50)
    print("   🚀 PROJECT SANJAYA v2.1 - MASTER LAUNCHER")
    print("="*50 + "\n")
    
    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)
    
    processes = {}
    
    try:
        # Start backend
        processes["backend"] = start_backend()
        time.sleep(5)  # Wait for backend to initialize
        
        # Start dashboards
        processes["child"] = start_streamlit("dashboard/child_app.py", STREAMLIT_CHILD_PORT)
        processes["parent"] = start_streamlit("dashboard/parent_app.py", STREAMLIT_PARENT_PORT)
        processes["admin"] = start_streamlit("dashboard/admin_app.py", STREAMLIT_ADMIN_PORT)
        time.sleep(3)  # Wait for dashboards
        
        # Start NGROK
        public_url = start_ngrok()
        
        # Test backend
        backend_url = f"http://localhost:{FASTAPI_PORT}"
        if not test_backend(backend_url):
            print("[ERROR] Backend failed to start properly")
            cleanup_processes(processes)
            sys.exit(1)
        
        # Create default admin
        create_default_admin()
        time.sleep(1)
        
        # Get admin token
        admin_token = get_admin_token()
        
        # Print URLs
        print_access_urls(public_url)
        
        # Print system status
        print_system_status(backend_url, admin_token)
        
        # Success message
        print("✨ [SYSTEM READY] Project Sanjaya v2.1 is running!")
        print("💡 Press Ctrl+C to stop all services\n")
        
        # Keep running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n⏹️  Shutdown requested...")
    
    except Exception as e:
        print(f"\n[ERROR] Fatal error: {e}")
    
    finally:
        cleanup_processes(processes)
        print("\n✓ Shutdown complete.\n")


if __name__ == "__main__":
    main()