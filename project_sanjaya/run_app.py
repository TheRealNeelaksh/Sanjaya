import subprocess
import sys
import time
import atexit

# --- Configuration ---
FLASK_APP_FILE = "main.py"
STREAMLIT_APP_FILE = "dashboard/app.py"
PYTHON_EXECUTABLE = sys.executable

# --- Global Process Management ---
processes = []

def cleanup():
    """Ensure all child processes are terminated on exit."""
    print("Shutting down all services...")
    for p in processes:
        if p.poll() is None: # If the process is still running
            p.terminate()
            p.wait()
    print("All services stopped.")

atexit.register(cleanup)

def run():
    """
    Launches the Flask backend and Streamlit frontend in parallel.
    """
    print("🚀 Launching Project Sanjaya...")

    # --- Launch Flask Backend ---
    try:
        print(f"Starting Flask backend from '{FLASK_APP_FILE}'...")
        flask_process = subprocess.Popen(
            [PYTHON_EXECUTABLE, FLASK_APP_FILE, "serve"],
            stdout=sys.stdout,
            stderr=sys.stderr
        )
        processes.append(flask_process)
        print(f"✅ Flask backend started with PID: {flask_process.pid}")
    except Exception as e:
        print(f"❌ Failed to start Flask backend: {e}")
        sys.exit(1)

    # Give the backend a moment to start up before launching the frontend
    time.sleep(5)

    # --- Launch Streamlit Frontend ---
    try:
        print(f"Starting Streamlit dashboard from '{STREAMLIT_APP_FILE}'...")
        streamlit_process = subprocess.Popen(
            [PYTHON_EXECUTABLE, "-m", "streamlit", "run", STREAMLIT_APP_FILE],
            stdout=sys.stdout,
            stderr=sys.stderr
        )
        processes.append(streamlit_process)
        print(f"✅ Streamlit dashboard started with PID: {streamlit_process.pid}")
    except Exception as e:
        print(f"❌ Failed to start Streamlit dashboard: {e}")
        sys.exit(1)

    print("\n🎉 Project Sanjaya is running!")
    print("➡️  Access the Streamlit dashboard in your browser.")
    print("➡️  Use the network URL from the backend logs on your mobile device to start tracking.")
    print("\nPress Ctrl+C in this window to stop all services.")

    # Keep the main script alive to monitor child processes
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Ctrl+C received.")
        sys.exit(0)

if __name__ == "__main__":
    run()