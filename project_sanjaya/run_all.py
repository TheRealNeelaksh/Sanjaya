import subprocess
import sys
import time
import os
import signal
from project_sanjaya.backend.database import SessionLocal, engine
from project_sanjaya.backend.models import Base
from project_sanjaya.backend.auth import admin_user_exists, register_user

def init_db():
    """Creates all database tables."""
    Base.metadata.create_all(bind=engine)

def create_admin_if_not_exists():
    """Checks if an admin user exists and creates one if not."""
    db = SessionLocal()
    if not admin_user_exists(db):
        print("Admin user not found. Creating a new one...")
        print("Please set a password for the admin user.")
        password = input("Enter password: ")
        register_user(db, "admin", password, "admin")
        print("Admin user created successfully.")
    db.close()

def run_commands():
    """
    Launches the backend server, ngrok tunnel, and all three Streamlit dashboards.
    """
    backend_cmd = "uvicorn project_sanjaya.backend.app:app --host 0.0.0.0 --port 8000"
    ngrok_cmd = "python project_sanjaya.scripts.ngrok_helper"
    streamlit_cmds = {
        "Child App": "streamlit run project_sanjaya/dashboard/child_app.py --server.port 8501",
        "Parent App": "streamlit run project_sanjaya/dashboard/parent_app.py --server.port 8502",
        "Admin App": "streamlit run project_sanjaya/dashboard/admin_app.py --server.port 8503",
    }

    processes = {}
    print("🚀 Starting backend and ngrok services...")

    # Set process creation flags for Windows
    creationflags = 0
    preexec_fn = None
    if sys.platform == "win32":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        preexec_fn = os.setsid

    # Start backend and ngrok
    processes["Backend"] = subprocess.Popen(
        backend_cmd.split(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=creationflags,
        preexec_fn=preexec_fn,
    )
    print(f"  -> Started Backend (PID: {processes['Backend'].pid})")

    processes["Ngrok"] = subprocess.Popen(
        ngrok_cmd.split(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=creationflags,
        preexec_fn=preexec_fn,
    )
    print(f"  -> Started Ngrok (PID: {processes['Ngrok'].pid})")

    try:
        # Wait for ngrok URL
        ngrok_url = ""
        for line in iter(processes["Ngrok"].stdout.readline, b''):
            line_str = line.decode('utf-8').strip()
            print(line_str)
            if "ngrok tunnel available at" in line_str:
                ngrok_url = line_str.split("at ")[-1]
                break

        # Set API_URL and start Streamlit apps
        env = os.environ.copy()
        env["API_URL"] = ngrok_url
        print(f"\n🚀 Starting Streamlit dashboards with API_URL: {ngrok_url}")

        for name, cmd in streamlit_cmds.items():
            process = subprocess.Popen(
                cmd.split(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=creationflags,
                preexec_fn=preexec_fn,
                env=env,
            )
            processes[name] = process
            print(f"  -> Started {name} (PID: {process.pid})")
            time.sleep(2)

        print("\n✅ All services are running!")
        print("\n--- Access URLs ---")
        print("Child Dashboard:  http://localhost:8501")
        print("Parent Dashboard: http://localhost:8502")
        print("Admin Dashboard:  http://localhost:8503")
        print("--------------------")
        print("\nBackend server logs and ngrok URL will be in the terminal where you ran this script.")
        print("Press Ctrl+C to shut down all services.")

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n🛑 Shutting down all services...")
        for name, process in processes.items():
            try:
                if sys.platform == "win32":
                    process.send_signal(signal.CTRL_BREAK_EVENT)
                else:
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                process.terminate()
                process.wait(timeout=5)
                print(f"  -> Terminated {name}")
            except (ProcessLookupError, TimeoutExpired, OSError):
                pass # Process already terminated
        print("✅ Shutdown complete.")
        sys.exit(0)

if __name__ == "__main__":
    init_db()
    create_admin_if_not_exists()
    run_commands()
