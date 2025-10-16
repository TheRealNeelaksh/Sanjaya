# 🚀 Deployment Instructions (Render & Streamlit Cloud)

This guide provides step-by-step instructions to deploy Project Sanjaya, making it publicly accessible. We will deploy the backend to **Render** and the dashboard to **Streamlit Community Cloud**.

---

### Part 1: Deploying the Backend to Render

Render will host our Python backend and provide a public URL for the tracking web page.

1.  **Sign Up & Connect GitHub:**
    *   Create a free account on [render.com](https://render.com).
    *   Connect your GitHub account and authorize it to access the `project_sanjaya` repository.

2.  **Create a New Web Service:**
    *   From your Render Dashboard, click **New +** -> **Web Service**.
    *   Select your `project_sanjaya` repository.
    *   Give your service a unique name (e.g., `sanjaya-tracker-backend`).

3.  **Configure the Service:**
    *   **Region:** Choose a region close to you.
    *   **Branch:** Select your main branch (e.g., `main` or `master`).
    *   **Build Command:** `pip install -r project_sanjaya/requirements.txt`
    *   **Start Command:** `waitress-serve --host=0.0.0.0 --port=$PORT main:app`
        *   *Note: Render automatically sets the `$PORT` environment variable.*

4.  **Add Environment Variables:**
    *   Before the first deployment, go to the **Environment** tab.
    *   Under "Secret Files", click **Add Secret File**.
    *   **Filename:** `project_sanjaya/.env`
    *   **Contents:**
        ```
        AVIATIONSTACK_KEY=YOUR_KEY_HERE
        ```
        (Replace with your actual AviationStack API key).

5.  **Deploy:**
    *   Click **Create Web Service**. Render will build and deploy your application.
    *   Once it's live, copy the public URL provided (e.g., `https://sanjaya-tracker-backend.onrender.com`). This is your **Backend URL**.

---

### Part 2: Deploying the Dashboard to Streamlit Cloud

Streamlit Community Cloud is the best place to host our dashboard.

1.  **Sign Up & Connect GitHub:**
    *   Create a free account at [streamlit.io/cloud](https://streamlit.io/cloud).
    *   Connect the same GitHub repository.

2.  **Deploy the App:**
    *   From your workspace, click **New app**.
    *   Select your repository and branch.
    *   Set the **Main file path** to `project_sanjaya/dashboard/app.py`.
    *   Give your app a custom URL (e.g., `my-sanjaya-dashboard`).

3.  **Add the Backend URL as a Secret:**
    *   In the "Advanced settings" section, add the following secret:
        *   **Key:** `BACKEND_URL`
        *   **Value:** Your **Backend URL** from Render (e.g., `https://sanjaya-tracker-backend.onrender.com`)

4.  **Deploy:**
    *   Click **Deploy!**. Your dashboard will be live in a few minutes.

---

### Final Workflow

*   To start a new trip, go to your **Render Backend URL**.
*   To view the live dashboard, go to your **Streamlit Cloud URL**. The "Reset Trip" button on the dashboard will now correctly communicate with your deployed backend.