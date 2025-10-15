# 🚀 Deployment Instructions for Project Sanjaya

To make Project Sanjaya accessible from anywhere, you need to deploy its two main components: the **Flask Backend** and the **Streamlit Dashboard**.

---

## 1. Deploying the Flask Backend

The Flask backend needs to be deployed to a web hosting service so that your mobile phone can access it from any network. A service like **Render** or **Heroku** is a good choice.

### Using Render (Recommended)

1.  **Sign up for a free account on [Render](https://render.com/).**
2.  **Create a `gunicorn` entry in `requirements.txt`**:
    Render uses Gunicorn to serve Flask apps. Add it to your `requirements.txt`:
    ```
    streamlit
    streamlit-folium
    geocoder
    requests
    python-dotenv
    Flask
    gunicorn
    ```
3.  **Create a New Web Service on Render**:
    *   Go to your Dashboard and click "New" -> "Web Service".
    *   Connect your GitHub repository where this project is stored.
4.  **Configure the Service**:
    *   **Name**: Give your service a name (e.g., `sanjaya-tracker-backend`).
    *   **Region**: Choose a region close to you.
    *   **Branch**: Select your main branch.
    *   **Build Command**: `pip install -r requirements.txt` (this is usually the default).
    *   **Start Command**: `gunicorn main:app`
5.  **Add Environment Variables**:
    *   Go to the "Environment" tab for your new service.
    *   Add a new secret file.
    *   **Filename**: `.env`
    *   **Contents**:
        ```
        AVIATIONSTACK_KEY="YOUR_REAL_API_KEY"
        ```
6.  **Deploy**:
    *   Click "Create Web Service". Render will build and deploy your app.
    *   Once deployed, you will get a public URL (e.g., `https://sanjaya-tracker-backend.onrender.com`). **This is the URL you will use on your phone.**

---

## 2. Deploying the Streamlit Dashboard

The Streamlit dashboard is best deployed using **Streamlit Community Cloud**.

1.  **Sign up for a free account on [Streamlit Community Cloud](https://streamlit.io/cloud).**
2.  **Push your code to a public GitHub repository.** (Streamlit Cloud requires this).
3.  **Deploy from Streamlit Cloud**:
    *   From your workspace, click "New app".
    *   Select the repository and branch you want to deploy.
    *   **Main file path**: `dashboard/app.py`
    *   Give your app a custom URL.
4.  **Important: Update the Backend URL**:
    The Streamlit app doesn't directly connect to the backend, but it's good practice to know where your backend is. The key is that the **phone** must be able to reach the **backend's public URL**.
5.  **Deploy**:
    *   Click "Deploy!". Your dashboard will be live in a few minutes.

---

## 🏁 Final Steps

1.  **Start a tracking session**:
    *   Navigate to your public **Flask backend URL** on your mobile phone (e.g., `https://sanjaya-tracker-backend.onrender.com`).
    *   Enter your details and start tracking.
2.  **View the dashboard**:
    *   Open your public **Streamlit dashboard URL** on any device to see the live tracking in action.

Your tracker is now live and accessible globally!