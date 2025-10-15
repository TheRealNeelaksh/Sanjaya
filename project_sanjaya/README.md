# 🛰️ Project Sanjaya — Jules Tracker (v1.1 "Odyssey")

**A highly robust, automated, live map dashboard showing your movement from Start → Airport → Flight → Destination → Home — updating in real time and connecting dots visually.**

This is the final, most stable version, using the Google Flights API via SerpApi for maximum reliability.

---

## 🚀 Features

- **Dual Public URLs**: Instantly generates secure, public `ngrok` URLs for both the **Tracking Link** and the **Live Dashboard**, making the entire application shareable.
- **Resilient Architecture**: Uses a non-blocking backend and a production-ready `Waitress` server to prevent crashes and ensure stability.
- **Accurate Flight Search**: Uses the Google Flights API (via SerpApi) with airline, flight number, departure/arrival airports, and date for the most reliable data.
- **Smart Dashboard Workflow**:
    - Includes a password-protected "Reset Trip" button to easily clear old data.
- **Auto-Refreshing Dashboard**: The dashboard automatically refreshes to show the latest data.
- **Flexible Trip Management**: Allows for multiple start/stop tracking "segments" within a single "trip".
- **Final Map Image**: Generates a PNG image of the complete trip map when the trip ends.

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
  - Add your SerpApi API key to the `.env` file: `SERPAPI_KEY="YOUR_KEY_HERE"`
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