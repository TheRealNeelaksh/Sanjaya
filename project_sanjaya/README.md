# 🛰️ Project Sanjaya — Jules Tracker (v0.5 "Conduit")

**A robust, automated, live map dashboard showing your movement from Start → Airport → Flight → Destination → Home — updating in real time and connecting dots visually.**

This version focuses on stability and a seamless user experience, with a production-ready server, automatic link generation, and a self-refreshing dashboard.

---

## 🚀 Features

- **Automatic Public URL**: Instantly generates a secure, public `ngrok` URL for the tracking web page. No more manual IP address sharing!
- **Auto-Refreshing Dashboard**: The Streamlit dashboard now automatically refreshes every 20 seconds, ensuring you always see the latest data.
- **Flexible Trip Management**: Start a "Trip," then begin and end multiple "Tracking Segments" within it (e.g., for a drive, then a walk).
- **Smart Flight Tracking**: Automatically fetches flight schedules and polls for live data only during the flight window to be more efficient.
- **Full Journey Visualization**: Tracks ground movement (via phone GPS) and air travel (via flight API) and displays the entire path on a single map.
- **Final Map Image**: Generates a PNG image of the complete trip map upon completion.

---

## ⚙️ How It Works

The system consists of two main components that run simultaneously:

1.  **The Waitress + Flask Backend (`run_app.py` -> `main.py`)**:
    *   A robust Waitress server runs the Flask application to serve the tracking web page, ensuring cross-platform compatibility.
    *   This page uses the browser's Geolocation API to get GPS coordinates.
    *   Receives user details and location data from the web page.
    *   Runs a background thread to monitor flight status using the AviationStack API.
    *   Logs all data to the `/logs` directory.

2.  **The Streamlit Dashboard (`dashboard/app.py`)**:
    *   Reads the session information and location data from the `/logs` directory.
    *   Presents a real-time visualization of the trip, including the map, user details, and status.

---

## 🛠️ Usage

### 1. Setup

- **Clone the repository.**
- **Install dependencies**:
  ```bash
  pip install -r requirements.txt
  ```
- **Set API & Ngrok Keys**:
  - Add your AviationStack API key to the `.env` file: `AVIATIONSTACK_KEY="YOUR_KEY_HERE"`
  - Add your ngrok authtoken to the `ngrok.yml` file. You can get a free token from the [ngrok Dashboard](https://dashboard.ngrok.com/get-started/your-authtoken).
    ```yaml
    # In ngrok.yml
    version: "2"
    authtoken: <YOUR_NGROK_AUTHTOKEN>
    ```

### 2. Running the Application

Simply run the unified launcher script:

```bash
python run_app.py
```

This single command will launch all services and automatically print your **unique, public tracking URL** to the console.

### 3. Start Tracking

1.  Open the public tracking URL (e.g., `https://<unique-id>.ngrok-free.app`) on your mobile phone's web browser.
2.  Fill in your trip details and press "Start Trip".
3.  View your progress on the Streamlit dashboard (usually at `http://localhost:8502`).

For deployment instructions, see `DEPLOYMENT.md`.