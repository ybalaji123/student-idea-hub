
# Deployment Guide

## 1. Backend Deployment (Render)

1.  **Push to GitHub**: Make sure this project is pushed to a GitHub repository.
2.  **Create New Web Service**: Go to [Render Dashboard](https://dashboard.render.com/), click "New +", and select "Web Service".
3.  **Connect GitHub**: Connect your GitHub account and select this repository.
4.  **Configure Service**:
    *   **Name**: `student-idea-hub-api` (or similar)
    *   **Runtime**: `Python 3`
    *   **Build Command**: `pip install -r requirements.txt`
    *   **Start Command**: `uvicorn backend.database:app --host 0.0.0.0 --port 10000`
5.  **Environment Variables**:
    *   Scroll down to "Environment Variables" and add:
        *   `Key`: `DATABASE_URL`
        *   `Value`: `postgresql://postgres.ddqnipwmeueypbkvaxoo:Yemineni%40123@aws-1-ap-south-1.pooler.supabase.com:6543/postgres`
        *   *(Note: This is your sensitive database connection string. Keep it secret!)*
    *   Add `PYTHON_VERSION` with value `3.10.0` (optional but recommended for stability).
6.  **Deploy**: Click "Create Web Service". Wait for the deployment to succeed.
7.  **Copy Backend URL**: Once deployed, copy the URL (e.g., `https://student-idea-hub-api.onrender.com`).

## 2. Frontend Deployment

1.  **Update Frontend Config**:
    *   Open `frontend/script.js`.
    *   Find the line: `const API_URL = "http://127.0.0.1:8000";`
    *   Change it to your new Render Backend URL:
        ```javascript
        const API_URL = "https://your-app-name.onrender.com"; 
        ```
2.  **Commit & Push**: Save the file and push the changes to GitHub.
3.  **Deploy via GitHub Pages**:
    *   Go to your GitHub repository settings.
    *   Go to "Pages" section.
    *   Select the `main` branch and `/frontend` folder (if possible, otherwise move frontend to root or use Netlify/Vercel).
    *   **Alternative (Netlify/Vercel)**:
        *   Drag and drop the `frontend` folder to Netlify Drop, or connect the repo and set the "Base directory" (`frontend`) and "Publish directory" (`.`).
4.  **Done!** Your app is now live.
