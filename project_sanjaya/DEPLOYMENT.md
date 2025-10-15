# 🚀 Vercel Deployment Instructions

This guide will walk you through deploying both the **Flask Backend** and the **Streamlit Dashboard** to make Project Sanjaya publicly accessible.

---

### Part 1: Deploying the Backend to Vercel

1.  **Create a Vercel Account & Connect GitHub:**
    *   Sign up for a free account at [vercel.com](https://vercel.com).
    *   Connect your GitHub account and import the `project_sanjaya` repository.

2.  **Configure the Project:**
    *   Vercel will automatically detect the Python backend using the `vercel.json` file.
    *   Before deploying, go to the "Settings" tab for your new project.
    *   Click on "Environment Variables".
    *   Add your `AVIATIONSTACK_KEY` as a secret. Vercel will use the `.env` file for local development, but needs this for deployment.
        *   **Key:** `AVIATIONSTACK_KEY`
        *   **Value:** `YOUR_AVIATIONSTACK_KEY_HERE`

3.  **Deploy:**
    *   Go to the "Deployments" tab and trigger a new deployment for your main branch.
    *   Vercel will build and deploy your application. Once complete, you will get a public URL (e.g., `https://sanjaya-backend.vercel.app`). This is your **Backend URL**.

4.  **Set Up the Cron Job:**
    *   Navigate back to your project's `vercel.json` file in your code editor.
    *   Add the following `crons` section to the file. This tells Vercel to call your `/update_status` endpoint every 15 minutes.

    ```json
    {
        "version": 2,
        "builds": [
            { "src": "main.py", "use": "@vercel/python" }
        ],
        "routes": [
            { "src": "/(.*)", "dest": "main.py" }
        ],
        "crons": [
            {
                "path": "/update_status",
                "schedule": "*/15 * * * *"
            }
        ]
    }
    ```
    *   Commit and push this change to your GitHub repository. Vercel will automatically redeploy, and your cron job will be active.

---

### Part 2: Deploying the Dashboard to Streamlit Community Cloud

1.  **Create a Streamlit Cloud Account:**
    *   Sign up for a free account at [streamlit.io/cloud](https://streamlit.io/cloud).
    *   Connect the same GitHub repository.

2.  **Deploy the App:**
    *   Click "New app" and select your repository.
    *   Set the **Main file path** to `project_sanjaya/dashboard/app.py`.
    *   In the "Advanced settings", add the following secret:
        *   **Key:** `BACKEND_URL`
        *   **Value:** Your **Backend URL** from Vercel (e.g., `https://sanjaya-backend.vercel.app`)

3.  **Deploy:**
    *   Click "Deploy!". Your dashboard will be live in a few minutes.

---

### Final Workflow

*   To start a new trip, go to your **Vercel Backend URL**.
*   To view the live dashboard, go to your **Streamlit Cloud URL**.