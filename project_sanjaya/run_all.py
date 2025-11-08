import subprocess
import sys
import time
import os
from project_sanjaya.backend.database import SessionLocal
from project_sanjaya.backend.auth import admin_user_exists, register_user

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
    commands = {
        "Backend": "uvicorn project_sanjaya.backend.app:app --host 0.0.0.0 --port 8000",
        "Ngrok": "python project_sanjaya/scripts/ngrok_helper.py",
        "Child App": "streamlit run project_sanjaya/dashboard/child_app.py --server.port 8501",
        "Parent App": "streamlit run project_sanjaya/dashboard/parent_app.py --server.port 8502",
        "Admin App": "streamlit run project_sanjaya/dashboard/admin_app.py --server.port 8503",
    }

    processes = {}
    print("🚀 Starting all Project Sanjaya services...")

    for name, cmd in commands.items():
        # Using preexec_fn=os.setsid to create a new process group.
        # This allows us to terminate the entire group, including shell-spawned children.
        process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid)
        processes[name] = process
        print(f"  -> Started {name} (PID: {process.pid})")
        time.sleep(2) # Stagger the launches to prevent port conflicts

    print("\n✅ All services are running!")
    print("\n--- Access URLs ---")
    print("Child Dashboard:  http://localhost:8501")
    print("Parent Dashboard: http://localhost:8502")
    print("Admin Dashboard:  http://localhost:8503")
    print("--------------------")
    print("\nBackend server logs and ngrok URL will be in the terminal where you ran this script.")
    print("Press Ctrl+C to shut down all services.")

    try:
        # Wait for ngrok to print its URL
        ngrok_url = ""
        for line in iter(processes["Ngrok"].stdout.readline, b''):
            line_str = line.decode('utf-8').strip()
            print(line_str) # Print ngrok output in real-time
            if "ngrok tunnel available at" in line_str:
                ngrok_url = line_str.split("at ")[-1]
                break

        # Set the ngrok URL as an environment variable for the Streamlit apps
        os.environ["API_URL"] = ngrok_url

        # Keep the main script alive
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n🛑 Shutting down all services...")
        for name, process in processes.items():
            # Terminate the entire process group
            os.killpg(os.getpgid(process.pid), 15) # 15 = SIGTERM
            print(f"  -> Terminated {name}")
        print("✅ Shutdown complete.")
        sys.exit(0)

if __name__ == "__main__":
    create_admin_if_not_exists()
    run_commands()
