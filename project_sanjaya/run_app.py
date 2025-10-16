import subprocess
import sys
import time
import atexit
import os
import threading
from pyngrok import ngrok, conf

# Import the background thread functions
from main import time_based_status_thread

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
    Launches the backend, frontend, and a public ngrok tunnel for the tracking link.
    """
    print("🚀 Launching Project Sanjaya (Render Edition)...")

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

    # --- Start Background Threads ---
    status_updater = threading.Thread(target=time_based_status_thread, daemon=True)
    status_updater.start()
    print("✅ Time-based status updater thread started.")

    # --- Configure and start ngrok tunnel for Flask ---
    try:
        conf.get_default().config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), NGROK_CONFIG_FILE)

        print("Starting ngrok tunnel for tracking link...")
        global ngrok_tunnel
        ngrok_tunnel = ngrok.connect(FLASK_PORT, "http")
        public_url = ngrok_tunnel.public_url

        print("="*60)
        print(f"📲 YOUR PUBLIC TRACKING URL: {public_url}")
        print(f"🖥️  YOUR LOCAL DASHBOARD URL: http://localhost:{STREAMLIT_PORT}")
        print("="*60)
    except Exception as e:
        print(f"❌ Failed to start ngrok tunnel: {e}"); sys.exit(1)

    # --- Launch Streamlit Frontend ---
    try:
        print(f"Starting Streamlit dashboard...")
        streamlit_process = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", STREAMLIT_APP_FILE,
             "--server.port", str(STREAMLIT_PORT), "--",
             public_url],
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