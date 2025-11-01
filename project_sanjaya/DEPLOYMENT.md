# 🚀 Running Project Sanjaya Locally

This guide provides instructions for running the complete Project Sanjaya application on your local machine. The `run_app.py` script will start both the Flask backend and the Streamlit frontend, and `ngrok` will be used to create a public URL so you can access the tracking service from your mobile device.

---

##  Prerequisites

1.  **Python**: Make sure you have Python 3.8+ installed.
2.  **Dependencies**: Install the required Python packages by running the following command from the repository root:
    ```bash
    pip install -r project_sanjaya/requirements.txt
    ```

---

## Local Development with ngrok

To run the application, you will need a free `ngrok` account to expose your local server to the internet.

1.  **Sign up for ngrok**: Create a free account at [ngrok.com](https://ngrok.com/).
2.  **Get your authtoken**: Find your authtoken on your ngrok dashboard.
3.  **Configure ngrok**: Create a `project_sanjaya/ngrok.yml` file with the following content, replacing `[YOUR_AUTHTOKEN]` with your actual token:
    ```yml
    version: "2"
    authtoken: [YOUR_AUTHTOKEN]
    tunnels:
      project-sanjaya:
        proto: http
        addr: 5000
    ```
    *Note: `ngrok.yml` is included in `.gitignore`, so you don't have to worry about accidentally committing your secret token.*

---

## 🏁 Running the Application

1.  **Start the application** by running the following command from the repository root:
    ```bash
    python project_sanjaya/run_app.py
    ```
2.  **The script will output two URLs**:
    *   **Public Tracking URL**: This is the `ngrok` URL. Open this link on your **mobile phone** to start a trip and begin logging your location.
    *   **Local Dashboard URL**: This is a `localhost` URL. Open this link on your **computer** to view the live tracking dashboard.

Your local tracking system is now fully operational!
