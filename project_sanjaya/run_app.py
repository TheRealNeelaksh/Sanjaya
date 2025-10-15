import subprocess
import sys
import time
import atexit
import os
import threading
from pyngrok import ngrok, conf

# Import the Flask app and the flight tracker thread function
from main import app, flight_tracker_thread

# --- Configuration ---
FLASK_PORT = 5000 # Using a different port to avoid conflicts
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
    Launches the Flask app, ngrok tunnel, flight tracker, and Streamlit dashboard.
    """
    print("🚀 Launching Project Sanjaya (Conduit)...")

    # --- Configure and start ngrok ---
    try:
        print("Authenticating ngrok...")
        conf.get_default().config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), NGROK_CONFIG_FILE)

        print("Starting ngrok tunnel...")
        global ngrok_tunnel
        ngrok_tunnel = ngrok.connect(FLASK_PORT)
        public_url = ngrok_tunnel.public_url
        print("="*60)
        print(f"📲 YOUR PUBLIC TRACKING URL: {public_url}")
        print("="*60)
    except Exception as e:
        print(f"❌ Failed to start ngrok tunnel: {e}")
        sys.exit(1)

    # --- Start Flask App and Flight Tracker in Threads ---
    print("Starting Flask backend and flight tracker...")
    flask_thread = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=FLASK_PORT, use_reloader=False))
    flask_thread.daemon = True
    flask_thread.start()

    tracker_thread = threading.Thread(target=flight_tracker_thread)
    tracker_thread.daemon = True
    tracker_thread.start()

    # --- Launch Streamlit Frontend ---
    try:
        print(f"Starting Streamlit dashboard...")
        streamlit_process = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", STREAMLIT_APP_FILE, "--", public_url],
            stdout=sys.stdout, stderr=sys.stderr
        )
        processes.append(streamlit_process)
        print(f"✅ Streamlit dashboard started with PID: {streamlit_process.pid}")
    except Exception as e:
        print(f"❌ Failed to start Streamlit dashboard: {e}")
        sys.exit(1)

    print("\n🎉 Project Sanjaya is running!")
    print("➡️  Access the Streamlit dashboard in your browser.")
    print("\nPress Ctrl+C in this window to stop all services.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Ctrl+C received.")
        sys.exit(0)

if __name__ == "__main__":
    run()