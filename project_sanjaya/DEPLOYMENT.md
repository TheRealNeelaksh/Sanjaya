# 🚀 Deployment Instructions for Project Sanjaya on Google Cloud

This guide provides instructions for deploying Project Sanjaya to Google Cloud Run. This will make your application accessible from anywhere with a public URL.

---

## Local Development with ngrok

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
4.  **Run the app**:
    ```bash
    python project_sanjaya/run_app.py
    ```

---

## Prerequisites

1.  **Google Cloud SDK**: Make sure you have the [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) installed and configured on your local machine.
2.  **Enable APIs**: Enable the Cloud Run, Cloud Build, and Container Registry APIs for your Google Cloud project.
3.  **Authentication**: Authenticate the `gcloud` CLI with your Google Cloud account:
    ```bash
    gcloud auth login
    gcloud config set project [YOUR_PROJECT_ID]
    ```

---

## 1. Deploying the Flask Backend

### Build and Push the Docker Image

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
    Take note of the URL provided after deployment. This will be your public backend URL.

---

## 2. Deploying the Streamlit Frontend

### Build and Push the Docker Image

1.  **Build the Docker image**:
    ```bash
    gcloud builds submit --tag gcr.io/[YOUR_PROJECT_ID]/sanjaya-frontend -f Dockerfile.streamlit .
    ```

2.  **Deploy to Cloud Run**:
    ```bash
    gcloud run deploy sanjaya-frontend \
      --image gcr.io/[YOUR_PROJECT_ID]/sanjaya-frontend \
      --platform managed \
      --region us-central1 \
      --allow-unauthenticated \
      --update-env-vars BACKEND_URL=[YOUR_BACKEND_URL]
    ```
    Replace `[YOUR_BACKEND_URL]` with the URL of your deployed Flask backend.

---

## Preventing CLI Timeouts

The `gcloud` commands for building and deploying can sometimes take a while. To prevent timeouts, you can increase the timeout for `gcloud` commands:

```bash
gcloud config set core/http_timeout -1
```

This command disables the timeout, so your deployments won't fail due to long build times.

---

## 🏁 Final Steps

1.  **Start a tracking session**:
    *   Navigate to your public **Flask backend URL** on your mobile phone.
    *   Enter your details and start tracking.
2.  **View the dashboard**:
    *   Open your public **Streamlit dashboard URL** on any device to see the live tracking in action.

Your tracker is now live and accessible globally!
