import subprocess
import sys
import time
import atexit
import os
import threading
from pyngrok import ngrok, conf

# Import the flight tracker thread function
from main import flight_tracker_thread

# --- Configuration ---
FLASK_PORT = 5000
STREAMLIT_PORT = 8501
WAITRESS_THREADS = 8
FLASK_APP_MODULE = "main:app"
STREAMLIT_APP_FILE = "dashboard/app.py"
NGROK_CONFIG_FILE = "ngrok.yml"

# --- Global Process Management ---
processes = []
ngrok_tunnels = []

def cleanup():
    """Ensure all child processes and ngrok tunnels are terminated on exit."""
    print("Shutting down all services...")
    for p in processes:
        if p.poll() is None:
            p.terminate()
            p.wait()
    for tunnel in ngrok_tunnels:
        ngrok.disconnect(tunnel.public_url)
    print("All services stopped.")

atexit.register(cleanup)

def run():
    """
    Launches the backend, frontend, and two public ngrok tunnels.
    """
    print("🚀 Launching Project Sanjaya (Oracle)...")

    # --- Start Waitress Server ---
    try:
        waitress_process = subprocess.Popen([
            "waitress-serve", f"--threads={WAITRESS_THREADS}",
            f"--host=0.0.0.0", f"--port={FLASK_PORT}", FLASK_APP_MODULE
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        processes.append(waitress_process)
        print(f"✅ Waitress server started with PID: {waitress_process.pid}")
    except Exception as e:
        print(f"❌ Failed to start Waitress: {e}"); sys.exit(1)

    # --- Start Flight Tracker Thread ---
    tracker_thread = threading.Thread(target=flight_tracker_thread, daemon=True)
    tracker_thread.start()
    print("✅ Flight tracker thread started.")

    # --- Configure and start ngrok tunnels ---
    try:
        conf.get_default().config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), NGROK_CONFIG_FILE)

        print("Starting ngrok tunnels...")
        flask_tunnel = ngrok.connect(FLASK_PORT, "http")
        streamlit_tunnel = ngrok.connect(STREAMLIT_PORT, "http")
        ngrok_tunnels.extend([flask_tunnel, streamlit_tunnel])

        print("="*60)
        print(f"📲 PUBLIC TRACKING URL: {flask_tunnel.public_url}")
        print(f"🖥️  PUBLIC DASHBOARD URL: {streamlit_tunnel.public_url}")
        print("="*60)
    except Exception as e:
        print(f"❌ Failed to start ngrok tunnels: {e}"); sys.exit(1)

    # --- Launch Streamlit Frontend ---
    try:
        print(f"Starting Streamlit dashboard...")
        streamlit_process = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", STREAMLIT_APP_FILE,
             "--server.port", str(STREAMLIT_PORT), "--",
             flask_tunnel.public_url, streamlit_tunnel.public_url],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        processes.append(streamlit_process)
        print(f"✅ Streamlit dashboard started with PID: {streamlit_process.pid}")
    except Exception as e:
        print(f"❌ Failed to start Streamlit dashboard: {e}"); sys.exit(1)

    print(f"\n🎉 Project Sanjaya is running!")
    print("Press Ctrl+C in this window to stop all services.")

    try:
        waitress_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Ctrl+C received.")
        sys.exit(0)

if __name__ == "__main__":
    run()