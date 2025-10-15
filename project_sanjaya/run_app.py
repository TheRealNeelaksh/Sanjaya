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
ngrok_tunnel = None

def cleanup():
    """Ensure all child processes and ngrok tunnels are terminated on exit."""
    print("Shutting down all services...")
    for p in processes:
        if p.poll() is None:
            p.terminate()
            p.wait()
    if ngrok_tunnel:
        ngrok.disconnect(ngrok_tunnel.public_url)
    print("All services stopped.")

atexit.register(cleanup)

def run():
    """
    Launches Waitress, the flight tracker, ngrok, and Streamlit.
    """
    print("🚀 Launching Project Sanjaya (Conduit)...")

    # --- Start Waitress Server ---
    try:
        print(f"Starting Waitress server for {FLASK_APP_MODULE}...")
        waitress_process = subprocess.Popen([
            "waitress-serve",
            f"--threads={WAITRESS_THREADS}",
            f"--host=0.0.0.0",
            f"--port={FLASK_PORT}",
            FLASK_APP_MODULE
        ], stdout=sys.stdout, stderr=sys.stderr)
        processes.append(waitress_process)
        print(f"✅ Waitress server started with PID: {waitress_process.pid}")
    except Exception as e:
        print(f"❌ Failed to start Waitress: {e}. Is waitress installed?")
        sys.exit(1)

    # --- Start Flight Tracker Thread ---
    print("Starting flight tracker thread...")
    tracker_thread = threading.Thread(target=flight_tracker_thread, daemon=True)
    tracker_thread.start()

    # --- Configure and start ngrok ---
    try:
        print("Starting ngrok tunnel...")
        conf.get_default().config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), NGROK_CONFIG_FILE)
        global ngrok_tunnel
        ngrok_tunnel = ngrok.connect(FLASK_PORT)
        public_url = ngrok_tunnel.public_url
        print("="*60)
        print(f"📲 YOUR PUBLIC TRACKING URL: {public_url}")
        print("="*60)
    except Exception as e:
        print(f"❌ Failed to start ngrok tunnel: {e}")
        sys.exit(1)

    # --- Launch Streamlit Frontend ---
    try:
        print(f"Starting Streamlit dashboard...")
        streamlit_process = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", STREAMLIT_APP_FILE, "--server.port", str(STREAMLIT_PORT), "--", public_url],
            stdout=sys.stdout, stderr=sys.stderr
        )
        processes.append(streamlit_process)
        print(f"✅ Streamlit dashboard started with PID: {streamlit_process.pid}")
    except Exception as e:
        print(f"❌ Failed to start Streamlit dashboard: {e}")
        sys.exit(1)

    print(f"\n🎉 Project Sanjaya is running! Dashboard at http://localhost:{STREAMLIT_PORT}")
    print("Press Ctrl+C in this window to stop all services.")

    try:
        waitress_process.wait() # Keep the main script alive
    except KeyboardInterrupt:
        print("\n🛑 Ctrl+C received.")
        sys.exit(0)

if __name__ == "__main__":
    run()