import subprocess
import sys
import time
import os
import signal
from project_sanjaya.backend.database import SessionLocal, engine
from project_sanjaya.backend.models import Base
from project_sanjaya.backend.auth import register_user
from project_sanjaya.backend.models import User


def init_db():
    """Creates all database tables."""
    Base.metadata.create_all(bind=engine)
    print("Database initialized.")


def create_admin(force_reset=False):
    """Creates or resets the admin user."""
    db = SessionLocal()
    existing = db.query(User).filter(User.username == "neelaksh").first()

    if existing and not force_reset:
        print("Admin user already exists.")
        db.close()
        return

    if existing and force_reset:
        print("Resetting existing admin user...")
        db.query(User).filter(User.username == "neelaksh").delete()
        db.commit()

    print("Creating admin user with default credentials...")
    register_user(db, "neelaksh", "neelakshisadmin", "admin")
    db.commit()
    print("✅ Admin user 'neelaksh' created successfully.")
    db.close()


def run_commands():
    """
    Launches the backend server, ngrok tunnel, and the main Streamlit dashboard.
    """
    backend_cmd = ["uvicorn", "project_sanjaya.backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
    ngrok_cmd = [sys.executable, "-u", "-m", "project_sanjaya.scripts.ngrok_helper"]
    main_app_cmd = ["streamlit", "run", "project_sanjaya/dashboard/main_app.py", "--server.port", "8501"]

    processes = {}
    print("🚀 Starting backend and ngrok services...")

    creationflags = 0
    preexec_fn = None
    if sys.platform == "win32":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        preexec_fn = os.setsid

    # --- Backend ---
    processes["Backend"] = subprocess.Popen(
        backend_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=creationflags,
        preexec_fn=preexec_fn,
    )
    print(f"  -> Started Backend (PID: {processes['Backend'].pid})")

    # --- Ngrok ---
    print("Attempting to start ngrok...")
    processes["Ngrok"] = subprocess.Popen(
        ngrok_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,  # Merge stderr into stdout
        creationflags=creationflags,
        preexec_fn=preexec_fn,
    )
    print(f"  -> Started Ngrok (PID: {processes['Ngrok'].pid})")

    try:
        ngrok_url = ""
        start_time = time.time()
        print("--- Reading ngrok process output ---")
        while time.time() - start_time < 20:
            line = processes["Ngrok"].stdout.readline()
            if not line:
                time.sleep(0.5)
                continue
            line_str = line.decode("utf-8", errors="ignore").strip()
            print(f"ngrok: {line_str}")
            if "ngrok tunnel available at" in line_str:
                ngrok_url = line_str.split("at ")[-1]
                print(f"--- Found ngrok URL: {ngrok_url} ---")
                break

        if not ngrok_url:
            print("\n❌ ERROR: Could not get ngrok URL after 20 seconds.")
            print("Please check the ngrok output above for errors.")
            for name, process in processes.items():
                process.terminate()
            sys.exit(1)

        env = os.environ.copy()
        env["API_URL"] = ngrok_url
        print(f"\n🚀 Starting Streamlit dashboard with API_URL: {ngrok_url}")

        # --- Main App ---
        processes["Main App"] = subprocess.Popen(
            main_app_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=creationflags,
            preexec_fn=preexec_fn,
            env=env,
        )
        print(f"  -> Started Main App (PID: {processes['Main App'].pid})")

        print("\n✅ All services are running!")
        print("Main Dashboard: http://localhost:8501")
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
            except (ProcessLookupError, subprocess.TimeoutExpired, OSError):
                pass
        print("✅ Shutdown complete.")
        sys.exit(0)


if __name__ == "__main__":
    init_db()
    # Set to True to reset the admin user every time (for development)
    # Set to False once everything is working
    create_admin(force_reset=True)
    run_commands()
