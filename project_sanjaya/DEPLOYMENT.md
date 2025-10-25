# 🚀 Deployment Instructions for Project Sanjaya

This guide provides two options for deploying Project Sanjaya to make it accessible from anywhere with a public URL: **Google Cloud (Recommended)** and a **Free Tier Alternative (Render + Streamlit Cloud)**.

---
---

## Option 1: Deploying on Google Cloud (Recommended)

This is the most robust and scalable option. The services have a generous free tier, but you will need to associate a billing account.

### Local Development with ngrok
Before deploying, you can run the application locally using ngrok to get a public URL for testing.
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
4.  **Run the app**: `python project_sanjaya/run_app.py`

### GCP Prerequisites
1.  **Google Cloud SDK**: Install and configure the [Google Cloud SDK](https://cloud.google.com/sdk/docs/install).
2.  **Enable APIs**: Enable the Cloud Run, Cloud Build, and Container Registry APIs.
3.  **Authentication**: Authenticate the `gcloud` CLI:
    ```bash
    gcloud auth login
    gcloud config set project [YOUR_PROJECT_ID]
    ```

### Step 1: Deploy the Flask Backend
1.  **Build the Docker image**:
    ```bash
    gcloud builds submit --tag gcr.io/[YOUR_PROJECT_ID]/sanjaya-backend -f Dockerfile.flask .
    ```
2.  **Deploy to Cloud Run**:
    ```bash
    gcloud run deploy sanjaya-backend \
      --image gcr.io/[YOUR_PROJECT_ID]/sanjaya-backend \
      --platform managed \
      --region us-central1 \
      --allow-unauthenticated
    ```
    **➡️ Copy the URL provided after deployment. This is your public backend URL.**

### Step 2: Deploy the Streamlit Frontend
1.  **Build the Docker image**:
    ```bash
    gcloud builds submit --tag gcr.io/[YOUR_PROJECT_ID]/sanjaya-frontend -f Dockerfile.streamlit .
    ```
2.  **Deploy to Cloud Run**, making sure to set the `BACKEND_URL` environment variable:
    ```bash
    gcloud run deploy sanjaya-frontend \
      --image gcr.io/[YOUR_PROJECT_ID]/sanjaya-frontend \
      --platform managed \
      --region us-central1 \
      --allow-unauthenticated \
      --set-env-vars BACKEND_URL=[PASTE_YOUR_BACKEND_URL_HERE]
    ```

### Preventing CLI Timeouts
To prevent timeouts during long builds, run: `gcloud config set core/http_timeout -1`

---
---

## Option 2: Free Tier Deployment (No Credit Card Required)

This option uses separate free services for the backend and frontend.

### Step 1: Deploy the Flask Backend to Render
1.  **Push your code to a GitHub repository.**
2.  **Sign up for [Render](https://render.com/)** using your GitHub account.
3.  **Create a New Web Service** on your Render dashboard and connect it to your repository.
4.  **Configure the Service**:
    *   **Environment**: `Python`
    *   **Build Command**: `pip install -r project_sanjaya/requirements.txt`
    *   **Start Command**: `gunicorn --chdir project_sanjaya main:app`
5.  **Deploy the service.** Once it's live, Render will give you a public URL.
    **➡️ Copy this URL. This is your backend URL.**

### Step 2: Deploy the Streamlit Dashboard to Streamlit Community Cloud
1.  **Ensure your code is in a public GitHub repository.**
2.  **Sign up for [Streamlit Community Cloud](https://streamlit.io/cloud)** using your GitHub account.
3.  **Deploy a New App**:
    *   Select your repository and branch.
    *   **Main file path**: `project_sanjaya/dashboard/app.py`
4.  **Set the Environment Variable**:
    *   Before deploying, go to the **Advanced settings**.
    *   In the **Secrets** section, add a new secret:
        *   **Name**: `BACKEND_URL`
        *   **Value**: `[PASTE_THE_BACKEND_URL_FROM_RENDER_HERE]`
5.  **Deploy!** Your dashboard will now be live and will fetch data from your backend on Render.

---

## 🏁 Final Usage Steps

1.  **Start a tracking session**: Navigate to your public **Flask backend URL** on your mobile phone and start a trip.
2.  **View the dashboard**: Open your public **Streamlit dashboard URL** on any device to see the live tracking.
