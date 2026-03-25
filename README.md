# CareerOS — Job Hunt Command Center

A full-stack AI-powered job hunting system with 6 specialized agents and a Kanban job tracker.

**[📖 User Guide](USER_GUIDE.md)** — How to maximize functionality (workflow, pro tips, agent usage)

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the app
```bash
streamlit run app.py
```

### 3. Open in browser
Streamlit will open at: `http://localhost:8501`

### 4. Enter your API key
Set `ANTHROPIC_API_KEY` as an environment variable or in a `.env` file. See "Environment Variable Support" below.

### 5. (Optional) Connect Google Calendar
To let the Career Coach plan your schedule:
1. Go to [Google Cloud Console](https://console.cloud.google.com/) → Create a project → Enable **Google Calendar API**
2. Create OAuth credentials: **APIs & Services → Credentials → Create OAuth 2.0 Client ID → Desktop app**
3. Download the JSON and save it as `google_credentials.json` in the project folder
4. In the app: **Profile → Connect Google Calendar** — sign in and grant access

---

## Quick Start

1. **Profile** → Fill in your resume, learning style, and goals  
2. **Job Tracker** → Add your job applications, paste JDs into each job  
3. **Career Coach** → Get your pipeline analyzed and an action plan  
4. **Resume Reviewer** → Tailor your resume to specific JDs  
5. **Gap Identifier** → Get an honest fit score + what to fix  
6. **Interview Coach** → Run mock interviews with real-time feedback  
7. **Study Planner** → Build a prioritized learning curriculum  
8. **Study Partner** → Learn concepts in your preferred style  

---

## Deploying (So You Can Access Anywhere)

### Option A: Streamlit Community Cloud (free, easiest)
1. Push this folder to a GitHub repo
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Deploy from your repo
4. Add your API key in the Streamlit Secrets manager:
   ```toml
   ANTHROPIC_API_KEY = "sk-ant-..."
   ```
5. Done — shareable URL, always online

### Option B: Railway / Render (free tier)
1. Push to GitHub
2. Connect to Railway.app or Render.com
3. Set `ANTHROPIC_API_KEY` as an environment variable
4. Deploy

### Option C: Local + ngrok (for quick sharing)
```bash
streamlit run app.py &
ngrok http 8501
```

---

## Environment Variable Support
If you set `ANTHROPIC_API_KEY` as an environment variable or Streamlit secret,
the app will auto-detect it. Add this to `app.py` if deploying to the cloud:

```python
import os
if not st.session_state.api_key:
    st.session_state.api_key = os.environ.get("ANTHROPIC_API_KEY", "") or st.secrets.get("ANTHROPIC_API_KEY", "")
```
