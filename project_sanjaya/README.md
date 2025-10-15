# 🛰️ Project Sanjaya — Jules Tracker (v0.2 "Guardian")

**A live map dashboard showing your movement from Start → Airport → Flight → Destination → Home — updating in real time and connecting dots visually.**

This version has been upgraded to a full client-server application for precise, mobile-based GPS tracking.

---

## 🚀 Features

- **Mobile GPS Tracking**: Generates a web link to be opened on a mobile device for precise location access.
- **User & Flight Details**: The web interface captures the user's name, flight number, and PNR to initialize a session.
- **Automated Mode Switching**:
    - **Ground Tracking**: Tracks your location via the phone's GPS.
    - **Airport Geofencing**: Automatically detects when you enter an airport's perimeter and updates the status.
    - **In-Flight Tracking**: Switches to the AviationStack API to track the flight's progress, pausing phone GPS to save battery.
    - **Landing Detection**: Detects when the flight has landed and seamlessly resumes ground tracking.
- **Live Dashboard**: A Streamlit dashboard visualizes the entire journey, showing the live path, user details, and current status (e.g., 🟢 Active, ✈️ At Airport, 🛫 In Flight, 🛬 Landed).
- **Start/Stop Control**: The web interface has buttons to start and stop the tracking session.
- **Trip Summary**: Generates a summary of the trip's duration and distance upon completion.

---

## ⚙️ How It Works

The system consists of two main components that run simultaneously:

1.  **The Flask Backend (`main.py`)**:
    *   Serves a web page (`templates/index.html`) to the user's mobile device.
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
- **Set API Key**:
  - Rename `.env.example` to `.env`.
  - Add your AviationStack API key to the `.env` file:
    ```
    AVIATIONSTACK_KEY="YOUR_KEY_HERE"
    ```

### 2. Running the Application

You need to run two processes in separate terminal windows.

- **Terminal 1: Start the Backend Server**
  ```bash
  python main.py serve
  ```
  This will start the Flask server. Note the network URL it provides (e.g., `http://192.168.1.5:8080`).

- **Terminal 2: Start the Streamlit Dashboard**
  ```bash
  streamlit run dashboard/app.py
  ```

### 3. Start Tracking

1.  Open the network URL from the backend server (e.g., `http://192.168.1.5:8080`) on your mobile phone's web browser.
2.  Fill in your name and flight details.
3.  Press "Start Tracking".
4.  View your progress on the Streamlit dashboard on your computer.

For deployment instructions, see `DEPLOYMENT.md`.