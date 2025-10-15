import subprocess
import sys
import time
import atexit
import os
import threading
from pyngrok import ngrok

# --- Configuration ---
FLASK_PORT = 8080
FLASK_APP_FILE = "main.py"
STREAMLIT_APP_FILE = "dashboard/app.py"
PYTHON_EXECUTABLE = sys.executable

# --- Global Process Management ---
processes = []
ngrok_tunnel = None

def cleanup():
    """Ensure all child processes and ngrok tunnels are terminated on exit."""
    print("Shutting down all services...")
    # Terminate subprocesses
    for p in processes:
        if p.poll() is None:
            p.terminate()
            p.wait()
    # Disconnect ngrok
    if ngrok_tunnel:
        ngrok.disconnect(ngrok_tunnel.public_url)
    print("All services stopped.")

atexit.register(cleanup)

def start_flask_app():
    """Starts the Flask backend in a subprocess."""
    try:
        print(f"Starting Flask backend from '{FLASK_APP_FILE}'...")
        flask_process = subprocess.Popen(
            [PYTHON_EXECUTABLE, FLASK_APP_FILE, "serve"],
            stdout=sys.stdout,
            stderr=sys.stderr
        )
        processes.append(flask_process)
        print(f"✅ Flask backend started with PID: {flask_process.pid}")
        return flask_process
    except Exception as e:
        print(f"❌ Failed to start Flask backend: {e}")
        sys.exit(1)

def start_streamlit_app():
    """Starts the Streamlit dashboard in a subprocess."""
    try:
        print(f"Starting Streamlit dashboard from '{STREAMLIT_APP_FILE}'...")
        # To avoid port conflicts if Streamlit defaults to 8080, we can specify a different port
        streamlit_process = subprocess.Popen(
            [PYTHON_EXECUTABLE, "-m", "streamlit", "run", STREAMLIT_APP_FILE, "--server.port", "8502"],
            stdout=sys.stdout,
            stderr=sys.stderr
        )
        processes.append(streamlit_process)
        print(f"✅ Streamlit dashboard started with PID: {streamlit_process.pid}")
        return streamlit_process
    except Exception as e:
        print(f"❌ Failed to start Streamlit dashboard: {e}")
        sys.exit(1)

def run():
    """
    Launches the Flask backend, creates a public ngrok tunnel, and starts the Streamlit frontend.
    """
    print("🚀 Launching Project Sanjaya (Pathfinder)...")

    # --- Start Flask App in a Thread ---
    # We run Flask in a thread within this script to allow ngrok to connect to it.
    flask_thread = threading.Thread(target=start_flask_app)
    flask_thread.daemon = True
    flask_thread.start()
    time.sleep(5) # Give the server a moment to start

    # --- Setup ngrok ---
    # Make sure to set your ngrok authtoken in your environment or directly.
    # On a new machine, you would run `ngrok config add-authtoken <YOUR_TOKEN>`
    try:
        authtoken = os.environ.get("NGROK_AUTHTOKEN")
        if authtoken:
            ngrok.set_auth_token(authtoken)
        else:
            print("⚠️  NGROK_AUTHTOKEN not found in environment. The tunnel may be rate-limited.")
            print("   To fix, get a token from dashboard.ngrok.com and run 'ngrok config add-authtoken <YOUR_TOKEN>'")

        global ngrok_tunnel
        ngrok_tunnel = ngrok.connect(FLASK_PORT)
        public_url = ngrok_tunnel.public_url
        print("" + "="*50)
        print(f"📲 YOUR PUBLIC TRACKING URL: {public_url}")
        print("" + "="*50)
    except Exception as e:
        print(f"❌ Failed to start ngrok tunnel: {e}")
        print("   Please ensure ngrok is installed and configured correctly.")
        sys.exit(1)

    # --- Start Streamlit App ---
    start_streamlit_app()

    print("\n🎉 Project Sanjaya is running!")
    print("➡️  Access the Streamlit dashboard in your browser (likely at http://localhost:8502).")
    print("➡️  Open the Public Tracking URL on your mobile device to start tracking.")
    print("\nPress Ctrl+C in this window to stop all services.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Ctrl+C received.")
        sys.exit(0)

if __name__ == "__main__":
    run()