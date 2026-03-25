import streamlit as st
import anthropic
import json
import os
from pathlib import Path

# Load .env if present (so ANTHROPIC_API_KEY works when set in .env)
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env", override=True)
except ImportError:
    pass
import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Optional

# ─── PAGE CONFIG ───
st.set_page_config(
    page_title="CareerOS",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CUSTOM CSS ───
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

/* Global */
[data-testid="stAppViewContainer"] { background: #080910; }
[data-testid="stSidebar"] { background: #0f1015 !important; border-right: 1px solid rgba(255,255,255,0.06); }
[data-testid="stSidebar"] > div:first-child { background: #0f1015 !important; }
body, .main, p, span, label, div { color: #eeedf0 !important; }
h1, h2, h3 { color: #c5f135 !important; font-family: 'Syne', sans-serif !important; }
h4, h5 { color: #eeedf0 !important; }

/* Inputs */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div > div {
    background: #161720 !important;
    border: 1px solid rgba(255,255,255,0.11) !important;
    color: #eeedf0 !important;
    border-radius: 8px !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #c5f135 !important;
    box-shadow: 0 0 0 1px #c5f135 !important;
}

/* Buttons */
.stButton > button {
    background: #c5f135 !important;
    color: #080910 !important;
    border: none !important;
    font-weight: 700 !important;
    font-family: 'Syne', sans-serif !important;
    border-radius: 8px !important;
    transition: all 0.15s !important;
}
.stButton > button:hover {
    background: #d6f760 !important;
    transform: scale(1.02);
}
.stButton > button p,
.stButton > button span,
.stButton > button div {
    color: #080910 !important;
}

/* Metrics */
[data-testid="stMetric"] {
    background: #161720;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 10px;
    padding: 16px !important;
}
[data-testid="stMetricLabel"] { color: #7a7a8c !important; font-size: 11px !important; }
[data-testid="stMetricValue"] { color: #eeedf0 !important; }

/* Chat messages */
.chat-msg-user {
    background: #1e2030;
    border: 1px solid rgba(255,255,255,0.11);
    border-radius: 10px;
    padding: 12px 16px;
    margin: 6px 0;
    margin-left: 60px;
    font-size: 18px;
    line-height: 1.65;
}
.chat-msg-agent {
    background: #161720;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 10px;
    padding: 12px 16px;
    margin: 6px 0;
    margin-right: 60px;
    font-size: 18px;
    line-height: 1.65;
}
.chat-label {
    font-size: 10px;
    font-family: 'IBM Plex Mono', monospace;
    color: #7a7a8c;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 4px;
}
.agent-label { color: #c5f135 !important; }

/* Status badges */
.badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 999px;
    font-size: 12px;
    font-family: 'IBM Plex Mono', monospace;
    font-weight: 500;
    margin: 2px;
}
.badge-wishlist { background: rgba(122,122,140,0.15); color: #7a7a8c; border: 1px solid rgba(122,122,140,0.3); }
.badge-applied { background: rgba(91,200,245,0.12); color: #5bc8f5; border: 1px solid rgba(91,200,245,0.3); }
.badge-screen { background: rgba(245,195,91,0.12); color: #f5c35b; border: 1px solid rgba(245,195,91,0.3); }
.badge-interview { background: rgba(165,91,245,0.12); color: #a55bf5; border: 1px solid rgba(165,91,245,0.3); }
.badge-offer { background: rgba(197,241,53,0.13); color: #c5f135; border: 1px solid rgba(197,241,53,0.3); }
.badge-rejected { background: rgba(245,91,122,0.12); color: #f55b7a; border: 1px solid rgba(245,91,122,0.3); }

/* Job cards */
.job-card {
    background: #161720;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 10px;
    padding: 14px 16px;
    margin: 6px 0;
    cursor: pointer;
    transition: all 0.15s;
}
.job-card:hover { border-color: rgba(255,255,255,0.2); }
.job-company { font-size: 18px; font-weight: 600; color: #eeedf0; }
.job-role { font-size: 12px; color: #7a7a8c; font-family: 'IBM Plex Mono', monospace; }

/* Sidebar nav */
.sidebar-section {
    font-size: 10px;
    font-family: 'IBM Plex Mono', monospace;
    color: rgba(122,122,140,0.7);
    letter-spacing: 0.14em;
    text-transform: uppercase;
    padding: 12px 0 4px;
}

/* Divider */
hr { border-color: rgba(255,255,255,0.06) !important; }

/* Expander */
.streamlit-expanderHeader { color: #eeedf0 !important; }
[data-testid="stExpander"] { background: #161720 !important; border: 1px solid rgba(255,255,255,0.08) !important; border-radius: 10px !important; }

/* Info/warning boxes */
.stAlert { border-radius: 8px !important; }

/* Selectbox */
[data-testid="stSelectbox"] > label { color: #7a7a8c !important; font-size: 12px !important; }

/* Number input */
.stNumberInput > div > div > input { background: #161720 !important; color: #eeedf0 !important; border-color: rgba(255,255,255,0.11) !important; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] { background: #0f1015; border-bottom: 1px solid rgba(255,255,255,0.06); gap: 0; }
.stTabs [data-baseweb="tab"] { color: #7a7a8c !important; background: transparent !important; border-bottom: 2px solid transparent !important; font-size: 13px !important; padding: 10px 20px !important; }
.stTabs [aria-selected="true"] { color: #eeedf0 !important; border-bottom-color: #c5f135 !important; }

/* Multiselect */
[data-testid="stMultiSelect"] > div > div { background: #161720 !important; border-color: rgba(255,255,255,0.11) !important; }

/* Logo */
.logo-text {
    font-family: 'Syne', sans-serif;
    font-size: 24px;
    font-weight: 700;
    color: #c5f135;
    letter-spacing: -0.5px;
}
.logo-sub {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    color: rgba(122,122,140,0.7);
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-top: 2px;
}
</style>
""", unsafe_allow_html=True)


# ─── SQLITE PERSISTENCE ───
DB_PATH = Path(__file__).parent / "careeros.db"

def _db():
    con = sqlite3.connect(str(DB_PATH))
    con.execute("""
        CREATE TABLE IF NOT EXISTS kv (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)
    con.commit()
    return con

def db_save(key: str, value) -> None:
    con = _db()
    con.execute(
        "INSERT OR REPLACE INTO kv (key, value) VALUES (?, ?)",
        (key, json.dumps(value, default=str))
    )
    con.commit()
    con.close()

def db_load(key: str, default=None):
    try:
        con = _db()
        row = con.execute("SELECT value FROM kv WHERE key=?", (key,)).fetchone()
        con.close()
        return json.loads(row[0]) if row else default
    except Exception:
        return default

def db_load_all() -> dict:
    """Load all persisted keys into a single dict on startup."""
    try:
        con = _db()
        rows = con.execute("SELECT key, value FROM kv").fetchall()
        con.close()
        return {k: json.loads(v) for k, v in rows}
    except Exception:
        return {}

# Per-job agents: Resume, Gap, Interview, Study are keyed by job_id. Coach & Partner are global.
PREP_AGENTS = ("resume", "gap", "interview", "study")
GLOBAL_AGENTS = ("coach", "partner")

def _migrate_conversations(raw: dict, jobs: list) -> dict:
    """Migrate old flat format to per-job format. Coach & Partner stay as lists."""
    out = {}
    out["coach"] = raw.get("coach", []) if isinstance(raw.get("coach"), list) else []
    out["partner"] = raw.get("partner", []) if isinstance(raw.get("partner"), list) else []

    def to_per_job(key: str) -> dict:
        val = raw.get(key, [])
        if isinstance(val, dict):
            return {int(k): v for k, v in val.items()}
        if not isinstance(val, list):
            val = []
        target_id = None
        jds_first = sorted(jobs, key=lambda j: (0 if j.get("jd") else 1, -j.get("created_at", 0)))
        if jds_first and jds_first[0].get("jd"):
            target_id = jds_first[0]["id"]
        elif jobs:
            target_id = jobs[0]["id"]
        if target_id is not None and val:
            return {str(target_id): val}
        return {}

    for k in PREP_AGENTS:
        out[k] = to_per_job(k)
    return out

# ─── STATE INIT ───
def init_state():
    # UI-only state (never persisted)
    ui_defaults = {
        "api_key": "",
        "current_page": "dashboard",
        "current_agent": "coach",
        "selected_job_id": None,
        "prep_job_id": None,  # Job selected for Resume/Gap/Interview/Study agents
    }
    for k, v in ui_defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # Persisted state — load from SQLite on first run this session
    if "_db_loaded" not in st.session_state:
        saved = db_load_all()
        st.session_state.profile = saved.get("profile", {
            "name": "", "role": "", "resume": "", "goals": ""
        })
        st.session_state.jobs = saved.get("jobs", [])
        st.session_state.next_job_id = saved.get("next_job_id", 1)
        raw_convos = saved.get("conversations", {})
        st.session_state.conversations = _migrate_conversations(raw_convos, saved.get("jobs", []))
        st.session_state._db_loaded = True

init_state()

def _normalize_api_key(raw_key: str) -> str:
    """Trim whitespace and a single layer of matching quotes."""
    key = (raw_key or "").strip()
    if len(key) >= 2 and key[0] == key[-1] and key[0] in {"'", '"'}:
        key = key[1:-1].strip()
    return key

def _read_env_api_key() -> str:
    key = _normalize_api_key(os.environ.get("ANTHROPIC_API_KEY", ""))
    if key:
        return key
    try:
        return _normalize_api_key(st.secrets.get("ANTHROPIC_API_KEY", ""))
    except Exception:
        return ""

def _looks_like_anthropic_key(key: str) -> bool:
    return key.startswith("sk-ant-")

DEFAULT_MAX_OUTPUT_TOKENS = 2400
MAX_CONTINUATIONS = 3
CONTINUE_PROMPT = "Continue exactly where you left off. Do not repeat earlier content. Finish the response."

def _extract_text_blocks(content_blocks) -> str:
    parts = []
    for block in content_blocks:
        if hasattr(block, "text") and block.text:
            parts.append(block.text)
    return "\n\n".join(parts).strip()

def _get_prep_messages(agent: str, job_id: int) -> list:
    convos = st.session_state.conversations
    if agent not in convos or not isinstance(convos[agent], dict):
        return []
    d = convos[agent]
    return d.get(str(job_id), d.get(job_id, []))  # JSON keys are strings

def _set_prep_messages(agent: str, job_id: int, messages: list) -> None:
    convos = st.session_state.conversations
    if agent not in convos or not isinstance(convos[agent], dict):
        convos[agent] = {}
    convos[agent][str(job_id)] = messages  # JSON keys are strings
    db_save("conversations", convos)

# ─── GOOGLE CALENDAR ───
GOOGLE_CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar"]
CALENDAR_CREDS_KEY = "google_calendar_credentials"

def get_calendar_credentials():
    """Load stored Google Calendar credentials. Returns Credentials or None."""
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        saved = db_load(CALENDAR_CREDS_KEY)
        if not saved or not isinstance(saved, dict):
            return None
        creds = Credentials.from_authorized_user_info(saved, GOOGLE_CALENDAR_SCOPES)
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            db_save(CALENDAR_CREDS_KEY, json.loads(creds.to_json()))
        return creds if creds.valid else None
    except Exception:
        return None

def is_calendar_connected() -> bool:
    return get_calendar_credentials() is not None

def connect_calendar_oauth() -> tuple[bool, str]:
    """Run OAuth flow. Returns (success, message)."""
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.oauth2.credentials import Credentials
        creds_path = Path(__file__).parent / "google_credentials.json"
        if not creds_path.exists():
            return False, (
                "Missing google_credentials.json. "
                "Download OAuth credentials from Google Cloud Console (APIs & Services → Credentials → Create OAuth 2.0 Client ID → Desktop app) "
                "and save as google_credentials.json in the project folder."
            )
        flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), GOOGLE_CALENDAR_SCOPES)
        creds = flow.run_local_server(port=0)
        db_save(CALENDAR_CREDS_KEY, json.loads(creds.to_json()))
        return True, "Google Calendar connected successfully."
    except Exception as e:
        return False, str(e)

def disconnect_calendar() -> None:
    con = _db()
    con.execute("DELETE FROM kv WHERE key = ?", (CALENDAR_CREDS_KEY,))
    con.commit()
    con.close()

def get_calendar_events(days_ahead: int = 7, max_results: int = 30) -> list[dict]:
    """Fetch upcoming events from primary calendar."""
    creds = get_calendar_credentials()
    if not creds:
        return []
    try:
        from googleapiclient.discovery import build
        from datetime import datetime, timezone, timedelta
        service = build("calendar", "v3", credentials=creds)
        now = datetime.now(timezone.utc).isoformat()
        time_max = (datetime.now(timezone.utc) + timedelta(days=days_ahead)).isoformat()
        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=now,
                timeMax=time_max,
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])
        out = []
        for e in events:
            start = e.get("start", {}) or {}
            start_str = start.get("dateTime") or start.get("date", "")
            out.append({"summary": e.get("summary", "(No title)"), "start": start_str})
        return out
    except Exception:
        return []

def create_calendar_event(title: str, start_datetime: str, end_datetime: str | None = None, description: str = "") -> tuple[bool, str]:
    """
    Create a calendar event. start_datetime and end_datetime in ISO format (YYYY-MM-DDTHH:MM or full).
    If end_datetime is None, default 1 hour.
    Returns (success, message).
    """
    creds = get_calendar_credentials()
    if not creds:
        return False, "Google Calendar not connected."
    try:
        from googleapiclient.discovery import build
        from datetime import datetime, timezone, timedelta
        service = build("calendar", "v3", credentials=creds)
        if not end_datetime:
            try:
                dt = datetime.fromisoformat(start_datetime.replace("Z", "+00:00"))
            except ValueError:
                dt = datetime.now(timezone.utc)
            end_dt = dt + timedelta(hours=1)
            end_datetime = end_dt.isoformat()
        if "T" not in start_datetime:
            start_datetime = start_datetime + "T09:00:00"
        if "T" not in end_datetime:
            end_datetime = end_datetime + "T10:00:00"
        if "+" not in start_datetime and not start_datetime.endswith("Z"):
            start_datetime += "Z"
        if "+" not in end_datetime and not end_datetime.endswith("Z"):
            end_datetime += "Z"
        body = {
            "summary": title,
            "start": {"dateTime": start_datetime, "timeZone": "UTC"},
            "end": {"dateTime": end_datetime, "timeZone": "UTC"},
        }
        if description:
            body["description"] = description
        service.events().insert(calendarId="primary", body=body).execute()
        return True, f"Created: {title}"
    except Exception as e:
        return False, str(e)

# Auto-load API key from environment or Streamlit secrets
env_key = _read_env_api_key()
if env_key and st.session_state.api_key != env_key:
    st.session_state.api_key = env_key

# ─── STATUS CONFIG ───
STATUSES = {
    "wishlist":  {"label": "Wishlist",      "color": "#7a7a8c", "icon": "◇", "badge": "badge-wishlist"},
    "applied":   {"label": "Applied",       "color": "#5bc8f5", "icon": "→", "badge": "badge-applied"},
    "screen":    {"label": "Phone Screen",  "color": "#f5c35b", "icon": "☎", "badge": "badge-screen"},
    "interview": {"label": "Interview",     "color": "#a55bf5", "icon": "✦", "badge": "badge-interview"},
    "offer":     {"label": "Offer",         "color": "#c5f135", "icon": "★", "badge": "badge-offer"},
    "rejected":  {"label": "Rejected",      "color": "#f55b7a", "icon": "✕", "badge": "badge-rejected"},
}

# ─── CLAUDE API ───
def get_client():
    key = _read_env_api_key() or _normalize_api_key(st.session_state.api_key)
    if key and st.session_state.api_key != key:
        st.session_state.api_key = key
    if not key:
        return None
    if not _looks_like_anthropic_key(key):
        return "invalid_format"
    return anthropic.Anthropic(api_key=key)

def call_claude(messages: list, system: str, max_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS) -> str:
    client = get_client()
    if not client:
        return "⚠️ No API key found. Set `ANTHROPIC_API_KEY` as an environment variable (e.g. `export ANTHROPIC_API_KEY=sk-ant-...`) and restart the app."
    if client == "invalid_format":
        return "⚠️ `ANTHROPIC_API_KEY` was loaded, but the value does not look like an Anthropic key. Update `.env` or your shell env and restart the app."
    try:
        msgs = list(messages)
        collected = []
        for _ in range(MAX_CONTINUATIONS + 1):
            response = client.messages.create(
                model="claude-opus-4-5",
                max_tokens=max_tokens,
                system=system,
                messages=msgs
            )
            text = _extract_text_blocks(response.content)
            if text:
                collected.append(text)
            if response.stop_reason != "max_tokens":
                return "\n\n".join(collected).strip()
            msgs.append({"role": "assistant", "content": response.content})
            msgs.append({"role": "user", "content": CONTINUE_PROMPT})
        return "\n\n".join(collected).strip()
    except anthropic.AuthenticationError:
        return "⚠️ Anthropic rejected the configured API key. Replace `ANTHROPIC_API_KEY` in `.env` (or your shell/Streamlit secret) with a current key and restart the app."
    except Exception as e:
        return f"⚠️ Error: {str(e)}"

def stream_claude(messages: list, system: str):
    client = get_client()
    if not client:
        yield "⚠️ No API key found. Set `ANTHROPIC_API_KEY` as an environment variable and restart the app."
        return
    if client == "invalid_format":
        yield "⚠️ `ANTHROPIC_API_KEY` was loaded, but the value does not look like an Anthropic key. Update `.env` or your shell env and restart the app."
        return
    try:
        with client.messages.stream(
            model="claude-opus-4-5",
            max_tokens=DEFAULT_MAX_OUTPUT_TOKENS,
            system=system,
            messages=messages
        ) as stream:
            for text in stream.text_stream:
                yield text
    except Exception as e:
        yield f"⚠️ Error: {str(e)}"

# ─── CALENDAR TOOLS (for Career Coach) ───
CALENDAR_TOOLS = [
    {
        "name": "get_calendar_events",
        "description": "Get the user's upcoming Google Calendar events. Use when planning their schedule, suggesting when to study, or checking availability. Returns event titles and start times.",
        "input_schema": {
            "type": "object",
            "properties": {
                "days_ahead": {"type": "integer", "description": "How many days ahead to fetch (default 7)", "default": 7},
            },
        },
    },
    {
        "name": "create_calendar_event",
        "description": "Create a new event on the user's Google Calendar. Use when the user wants to schedule study time, interview prep, application deadlines, or coaching follow-ups.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Event title"},
                "start_datetime": {"type": "string", "description": "Start in ISO format: YYYY-MM-DDTHH:MM or YYYY-MM-DD"},
                "end_datetime": {"type": "string", "description": "End in same format. If omitted, 1 hour after start."},
                "description": {"type": "string", "description": "Optional event description"},
            },
            "required": ["title", "start_datetime"],
        },
    },
]

def _run_calendar_tool(name: str, input_data: dict) -> str:
    if name == "get_calendar_events":
        days = input_data.get("days_ahead", 7)
        events = get_calendar_events(days_ahead=days)
        if not events:
            return "No upcoming events in that period."
        return "\n".join([f"- {e['start']}: {e['summary']}" for e in events])
    elif name == "create_calendar_event":
        title = input_data.get("title", "")
        start = input_data.get("start_datetime") or input_data.get("start")
        if not title or not start:
            return "Error: create_calendar_event requires 'title' and 'start_datetime' (e.g. 2025-03-21T14:00 or 2025-03-21)."
        ok, msg = create_calendar_event(
            title=title,
            start_datetime=start,
            end_datetime=input_data.get("end_datetime") or input_data.get("end"),
            description=input_data.get("description", ""),
        )
        return msg if ok else f"Error: {msg}"
    return "Unknown tool."

def call_claude_with_tools(messages: list, system: str, tools: list, max_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS) -> str:
    """Call Claude with tool use; executes tools and loops until done."""
    client = get_client()
    if not client:
        return "⚠️ No API key found. Set `ANTHROPIC_API_KEY` and restart."
    msgs = list(messages)
    max_rounds = 10
    continuation_count = 0
    collected = []
    for _ in range(max_rounds):
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=max_tokens,
            system=system,
            messages=msgs,
            tools=tools,
        )
        text = _extract_text_blocks(response.content)
        if text:
            collected.append(text)
        if response.stop_reason == "end_turn":
            return "\n\n".join(collected).strip()
        tool_results = []
        for block in response.content:
            if getattr(block, "type", None) == "tool_use":
                result = _run_calendar_tool(block.name, block.input)
                tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": result})
        if tool_results:
            msgs.append({"role": "assistant", "content": response.content})
            msgs.append({"role": "user", "content": tool_results})
            continue
        if response.stop_reason == "max_tokens" and continuation_count < MAX_CONTINUATIONS:
            continuation_count += 1
            msgs.append({"role": "assistant", "content": response.content})
            msgs.append({"role": "user", "content": CONTINUE_PROMPT})
            continue
        if collected:
            return "\n\n".join(collected).strip()
        msgs.append({"role": "assistant", "content": response.content})
    return "⚠️ Tool loop limit reached."

# ─── AGENT SYSTEM PROMPTS ───
def get_system_prompt(agent: str, job: dict | None = None) -> str:
    p = st.session_state.profile
    jobs = st.session_state.jobs

    jobs_summary = "\n".join([
        f"- {j['company']} | {j['role']} | {STATUSES[j['status']]['label']} | Applied: {j.get('date', 'unknown')}"
        + (f" | Notes: {j['notes']}" if j.get('notes') else "")
        for j in jobs
    ]) if jobs else "No applications tracked yet."

    active_jobs = [j for j in jobs if j['status'] in ('applied', 'screen', 'interview')]
    active_jds = "\n---\n".join([j['jd'] for j in active_jobs if j.get('jd')]) or "No JDs provided yet."

    # For per-job agents (resume, gap, interview, study), use the passed job
    if job:
        recent_jd = job.get('jd') or "Not provided yet."
        recent_company = job.get('company', 'target company')
        recent_role = job.get('role', 'target role')
    else:
        recent_jd_job = sorted(jobs, key=lambda x: x.get('created_at', 0), reverse=True)
        recent_jd_job = next((j for j in recent_jd_job if j.get('jd')), None)
        recent_jd = recent_jd_job['jd'] if recent_jd_job else "Not provided yet."
        recent_company = recent_jd_job['company'] if recent_jd_job else "target company"
        recent_role = recent_jd_job['role'] if recent_jd_job else "target role"

    if agent == "coach":
        base = f"""You are an elite career coach — part strategist, part analyst, part accountability partner. You operate in the TOP 10% of career coaches.

CANDIDATE PROFILE:
Name: {p['name'] or 'Not set — ask them'}
Target Role: {p['role'] or 'Not specified — ask them'}
Background & Resume:
{p['resume'] or 'Not provided — ask them to fill in their profile first'}
Goals: {p['goals'] or 'Not specified'}

LIVE JOB TRACKER DATA:
{jobs_summary}

YOUR COACHING PHILOSOPHY (follow strictly):

1. DIAGNOSE FIRST — Before giving advice, ask: "What's your goal?" and "What's blocking you?" 
   - Clarify: is this a skills gap, strategy problem, or execution problem?

2. PATTERN RECOGNITION — You have their tracker data. Use it. Spot things like:
   - "You've applied to 8 roles but only got responses from startups — that's a signal"
   - "Your application rate dropped 3 weeks ago — what happened?"
   - "You have interviews but no offers — it's a performance gap, not a pipeline gap"

3. OPTIONS OVER COMMANDS — Always give 2-3 paths, never just 1:
   - Option A: Safe/conservative
   - Option B: Ambitious
   - Option C: Fastest ROI

4. ACTION PLANS — End every substantive conversation with:
   - 1-3 concrete next steps
   - Clear timeline (today / this week / this month)

5. ACCOUNTABILITY — Reference their actual data by name. Flag stale applications (>3 weeks, no update).

6. THINK IN INCENTIVES:
   - Recruiters care about: risk reduction, speed, fit
   - Hiring managers care about: impact, ownership, can they do the job
   - Candidates care about: growth, comp, meaning

7. TRADE-OFF THINKING — Every recommendation has a cost. Name it:
   - "This gets you faster results but at the cost of ___"
   - "This is safer but means ___"

8. PERSONALIZE — Different people need different things:
   - Some need structure → give frameworks
   - Some need confidence → validate and reframe
   - Some need blunt truth → give it directly, with care

RULES:
- Ask max ONE clarifying question per turn
- Never give generic advice — always tie to their specific situation
- Reference their actual job applications when relevant
- Be warm but direct. Never lecture. Think out loud with them."""
        if is_calendar_connected():
            base += """

GOOGLE CALENDAR (connected):
You have access to the user's Google Calendar. Use it when:
- They ask you to plan their schedule, block study time, or add reminders
- You want to suggest concrete time slots — check get_calendar_events first to avoid conflicts
- They say things like "block time for...", "schedule...", "add to my calendar", "when should I..."
Use get_calendar_events to see their availability before creating events. Use create_calendar_event to add study blocks, interview prep, or application deadlines. Be proactive about scheduling when it supports their action plan."""
        return base

    elif agent == "resume":
        return f"""You are a world-class resume reviewer and rewriter for tech/AI roles. You think like a recruiter at top companies (Google, Stripe, Anthropic, Nasdaq).

YOUR REVIEW PHILOSOPHY:
Your goal is NOT grammar — your goal is to INCREASE INTERVIEW PROBABILITY.

CANDIDATE BACKGROUND:
{p['resume'] or 'Not provided — tell them to fill in their profile'}

TARGET: {recent_company} — {recent_role}
JOB DESCRIPTION:
{recent_jd}

THE 5-STEP REVIEW FRAMEWORK (use every time):

STEP 1 — 10-SECOND SCAN TEST
Ask yourself: "What story does this resume tell in 10 seconds?"
- Is the target role obvious?
- Is the tech stack visible?
- Is there impact/metrics?

STEP 2 — DIAGNOSE THE REAL PROBLEM (not surface issues)
Common root causes:
❌ No clear role signal (too broad)
❌ No impact — just tasks listed, no results
❌ Weak projects (no production, no scale, no ownership)
❌ Wrong alignment (experience doesn't match JD)

STEP 3 — BULLET STRUCTURE ENFORCEMENT
Strong bullet formula: ACTION + WHAT + HOW + IMPACT
Weak: "Built a fraud detection model"
Strong: "Built XGBoost fraud detection model on 550K transactions, achieving 90% recall and 0.6% FPR — reduced false alerts by 40%"
→ If no numbers: push them to estimate or use placeholders like [X%], [Xms]

STEP 4 — PRIORITIZE (top 3 changes that move the needle)
Never give 20 comments. Give:
1. The one structural fix
2. The key bullet rewrites
3. The missing signal to add

STEP 5 — REWRITE (this is key)
Don't just critique — show better versions:
Before → After for every suggested change

SIGNAL THINKING:
Each line must answer "Why should I interview this person?"
Strong signals: metrics, scale, production systems, ownership, specific tech
Weak signals: "familiar with", "worked on group project", vague tasks

ATS KEYWORD CHECK: Cross-reference JD keywords against resume. Flag every missing required skill.

POSITIONING STRATEGY: Advise on which version of their resume to use (SWE vs DS vs ML Engineer)."""

    elif agent == "gap":
        return f"""You are a brutally honest-but-constructive gap analyst for tech/AI job seekers.

CANDIDATE BACKGROUND:
{p['resume'] or 'Not provided'}

TARGET: {recent_company} — {recent_role}
JOB DESCRIPTION:
{recent_jd}

YOUR ANALYSIS FRAMEWORK:

REQUIRED OUTPUT FORMAT:
✅ STRENGTHS — Where candidate clearly matches JD (be specific, quote JD requirements)
❌ CRITICAL GAPS — Required skills/experience they lack (dealbreakers)
⚠️ MINOR GAPS — Nice-to-haves they're missing (closeable)
📊 FIT SCORE — X/10 with honest reasoning broken into: Technical Match / Experience Level / Project Signal / Keywords
🎯 STRATEGIC RECOMMENDATIONS — 
   • What to close before interview (with HOW)
   • What gaps to address head-on in interviews
   • What to omit or not emphasize
   • Repositioning advice if needed

THINK LIKE THIS:
- Recruiters scan for keywords + risk reduction
- Hiring managers look for: can they do this specific job?
- Be honest: a 6/10 with a clear path is more useful than false hope

Always end with: "The single most important thing to fix is: ___" """

    elif agent == "interview":
        return f"""You are a senior interviewer at {recent_company} conducting a real interview for: {recent_role}.

CANDIDATE BACKGROUND:
{p['resume'] or 'not provided'}

JOB DESCRIPTION:
{recent_jd}

YOUR INTERVIEW PHILOSOPHY:
You simulate REAL interviews — not casual practice chats. You create realistic conditions, evaluate like a hiring manager, and give high-signal feedback.

INTERVIEW STRUCTURE:
1. Set context (30 sec): state role, interview type, what you're evaluating
2. Main question (let them think — DON'T interrupt for 60+ seconds)
3. Follow-up probes:
   - "How would this scale to 10x users?"
   - "What are the failure cases?"
   - "What trade-offs did you consider?"
   - "Walk me through your reasoning"
4. Evaluate, then give structured feedback

FEEDBACK FORMAT (use every time after they answer):
✅ What they did well — specific, behavioral
⚠️ What needs improvement — specific, behavioral  
🚀 How to fix it — actionable technique, not "be better"

EVALUATION RUBRIC (score mentally on each):
• Problem understanding (did they clarify constraints?)
• Communication (clear structure? clear reasoning?)
• Technical correctness (right approach?)
• Depth & trade-offs (did they think beyond the surface?)
• Practical judgment (would this work in production?)

QUESTION MATCHING:
- For ML/DS roles: stats + modeling + deployment + trade-offs + business impact
- For SWE roles: coding + system design + scalability + failure modes
- For AI roles: LLM mechanics + RAG + fine-tuning + evaluation + latency/cost

ADVANCED TECHNIQUES:
- Use silence (let them think — don't fill the gap)
- Spot PATTERNS not just mistakes: "You tend to jump to solutions before clarifying — that's a pattern"
- Teach FRAMEWORKS not answers: "Here's how to approach this class of problem"
- Calibrate difficulty: slightly above their current level is the sweet spot

PRESSURE SIMULATION: Ask follow-ups that push harder. Real interviews probe until they find the edge."""

    elif agent == "study":
        # Per-job: focus on selected job's JD; otherwise use all active jobs
        if job:
            jd_context = f"TARGET: {recent_company} — {recent_role}\nJOB DESCRIPTION:\n{recent_jd}"
        else:
            apps = "\n".join([f"- {j.get('company', '')} ({j.get('role', '')})" for j in active_jobs]) or "none tracked yet"
            jd_context = f"ACTIVE APPLICATIONS:\n{apps}\n\nRELEVANT JOB DESCRIPTIONS:\n{active_jds}"
        return f"""You are an expert technical curriculum designer for competitive tech job seekers.

CANDIDATE BACKGROUND:
{p['resume'] or 'not provided'}
LEARNING APPROACH (hardcoded — apply always):
This candidate is a builder-strategist learner. They learn by PRODUCING, not consuming.
- Output-first: every topic must become an interview answer, project component, or explanation
- 3-layer system: Understand → Structure → APPLY (never stop at layer 2)
- Note template per topic: Intuition → System View → Trade-offs → Interview Answer → Code Example
- High ROI focus: what actually matters for interviews and projects, not comprehensive coverage
- Question bank over notes: collect "What is X?", "Why does X matter?", "When use X vs Y?"
- Mistake log: track patterns, not just individual errors
GOALS: {p['goals'] or 'not specified'}

{jd_context}

YOUR STUDY PLANNING SYSTEM — OUTPUT-FIRST LEARNING:

CORE PRINCIPLE: Don't build notes to "learn" — build notes to PERFORM (interviews, projects, explanations).

TOPIC CLASSIFICATION:
🔴 MUST KNOW — Will definitely be tested. Blocking if unknown. Study first.
🟡 SHOULD KNOW — Likely to come up. Important for depth.
🟢 GOOD TO KNOW — Bonus signal. Study last.

FOR EACH TOPIC, PROVIDE:
1. Why it matters for THIS specific role
2. What "mastery" looks like (can explain + code + discuss trade-offs)
3. Best FREE resource (specific: "CS329S Lecture 6", "Andrej Karpathy's makemore", not just "YouTube")
4. Time estimate to reach interview-ready level

STUDY SCHEDULE FORMAT:
Week 1: [foundational gaps]
Week 2: [role-specific depth]  
Week 3: [practice + mock interviews]
Week 4: [polish + edge cases]

THE 3-LAYER LEARNING SYSTEM:
Layer 1 — Understand (lecture/reading)
Layer 2 — Structure (concept notes with trade-offs)
Layer 3 — APPLY (project integration OR mock interview OR explain out loud)
→ Most people stop at Layer 2. Push to Layer 3 always.

OUTPUT-FIRST NOTE TEMPLATE (teach this):
For each concept: Intuition → System View → Trade-offs → Interview Answer → Code Example

ALWAYS END WITH: "The highest ROI thing to study first is ___" """

    elif agent == "partner":
        return f"""You are an adaptive study partner and technical tutor. Your #1 job is to teach in the way that makes THIS person actually understand and retain the material.

STUDENT PROFILE:
Name: {p['name'] or 'student'}
Background: {p['resume'] or 'not provided'}
Goals: {p['goals'] or 'not specified'}
Targets: {', '.join([f"{j['company']} ({j['role']})" for j in jobs[:5]]) or 'not specified'}

THIS STUDENT'S HARDCODED LEARNING PROFILE (apply without asking):
They are a builder-strategist learner — they learn by doing, not consuming.

DEFAULT TEACHING ORDER (use this sequence for every concept):
1. WHY it exists — what problem does it solve? (30 sec, no jargon)
2. INTUITION — one vivid analogy or mental model before any technical detail
3. SYSTEM VIEW — where does it fit? (e.g. "attention lives inside each transformer layer, which sits in the encoder stack")
4. TECHNICAL DETAIL — now the actual mechanism
5. TRADE-OFFS — pros/cons, when to use vs not use
6. INTERVIEW ANSWER — "here's your 30-second answer if they ask you this"
7. PROJECT CONNECTION — "here's how this applies to your [fraud system / RAG pipeline / CalPin]"
8. CODE SNIPPET — small, runnable, annotated (only after the above)

ADAPT DYNAMICALLY:
- If they say "I get it" too fast → probe with "explain it back to me"
- If they're lost → go back to the analogy, not more detail
- If they engage with code → give more code examples next time
- If they ask "why" questions → they need more context before mechanics

OUTPUT-FIRST TEACHING:
Every concept should produce USABLE OUTPUTS:
1. Interview answer (30-second version)
2. Project connection ("where would you use this in your fraud system / RAG pipeline?")
3. System-level understanding ("where does this fit in the ML pipeline?")

THE FEYNMAN METHOD (use always):
1. Explain at beginner level
2. Find where the explanation breaks down
3. Go back to the source
4. Simplify further

CHECK UNDERSTANDING CONSTANTLY:
- "Can you explain this back to me in your own words?"
- "What's still fuzzy?"
- "How would you use this in your [specific project]?"

MISTAKE LOG MINDSET:
When they get something wrong: 
- Don't just correct → find the PATTERN
- "You're confusing X with Y — here's the difference"
- "This is actually the same mistake as earlier with ___"

NEVER dump information. Teach interactively. One concept at a time. Connect everything to WHY it matters for their job search."""

    return "You are a helpful career assistant."

# ─── JOB HELPERS ───
def get_jobs():
    return st.session_state.jobs

def add_job(job_data: dict):
    job_data["id"] = st.session_state.next_job_id
    job_data["created_at"] = datetime.now().timestamp()
    job_data["progress"] = []
    st.session_state.jobs.append(job_data)
    st.session_state.next_job_id += 1
    db_save("jobs", st.session_state.jobs)
    db_save("next_job_id", st.session_state.next_job_id)

def update_job(job_id: int, updates: dict):
    for i, j in enumerate(st.session_state.jobs):
        if j["id"] == job_id:
            st.session_state.jobs[i].update(updates)
            break
    db_save("jobs", st.session_state.jobs)

def delete_job(job_id: int):
    st.session_state.jobs = [j for j in st.session_state.jobs if j["id"] != job_id]
    db_save("jobs", st.session_state.jobs)

def get_job(job_id: int) -> Optional[dict]:
    return next((j for j in st.session_state.jobs if j["id"] == job_id), None)

def job_stats():
    jobs = get_jobs()
    total = len([j for j in jobs if j["status"] != "wishlist"])
    active = len([j for j in jobs if j["status"] in ("applied", "screen", "interview")])
    interviews = len([j for j in jobs if j["status"] in ("interview", "offer")])
    offers = len([j for j in jobs if j["status"] == "offer"])
    screened = len([j for j in jobs if j["status"] not in ("wishlist", "applied")])
    rate = f"{round(screened/total*100)}%" if total > 0 else "—"
    return total, active, interviews, offers, rate

# ─── SIDEBAR ───
with st.sidebar:
    st.markdown('<div class="logo-text">CareerOS</div>', unsafe_allow_html=True)
    st.markdown('<div class="logo-sub">Job Hunt Command Center</div>', unsafe_allow_html=True)
    st.divider()

    # Navigation
    st.markdown('<div class="sidebar-section">Overview</div>', unsafe_allow_html=True)

    if st.button("◈  Dashboard", use_container_width=True):
        st.session_state.current_page = "dashboard"
        st.rerun()
    if st.button("⊞  Job Tracker", use_container_width=True):
        st.session_state.current_page = "tracker"
        st.rerun()

    st.markdown('<div class="sidebar-section">Career Coach</div>', unsafe_allow_html=True)
    if st.button("🧭  Career Coach", use_container_width=True):
        st.session_state.current_page = "agents"
        st.session_state.current_agent = "coach"
        st.rerun()

    st.markdown('<div class="sidebar-section">Job Preparation</div>', unsafe_allow_html=True)
    st.caption("Per-job · switch in dropdown")
    for icon, key, label in [
        ("✏️", "resume", "Resume Reviewer"),
        ("🔍", "gap", "Gap Identifier"),
        ("🎤", "interview", "Interview Coach"),
        ("📚", "study", "Study Planner"),
    ]:
        if st.button(f"{icon}  {label}", use_container_width=True):
            st.session_state.current_page = "agents"
            st.session_state.current_agent = key
            st.rerun()

    st.markdown('<div class="sidebar-section">Study</div>', unsafe_allow_html=True)
    if st.button("🤝  Study Partner", use_container_width=True):
        st.session_state.current_page = "agents"
        st.session_state.current_agent = "partner"
        st.rerun()

    st.markdown('<div class="sidebar-section">Settings</div>', unsafe_allow_html=True)
    if st.button("⚙  My Profile", use_container_width=True):
        st.session_state.current_page = "profile"
        st.rerun()

    # Mini stats
    st.divider()
    total, active, interviews, offers, rate = job_stats()
    st.markdown(f"""
    <div style="font-family:'IBM Plex Mono',monospace;font-size:12px;color:#7a7a8c;line-height:2;">
    📋 {total} applied &nbsp;·&nbsp; {active} active<br>
    🎤 {interviews} interviews &nbsp;·&nbsp; ★ {offers} offers<br>
    📊 {rate} response rate
    </div>
    """, unsafe_allow_html=True)

# ─── DASHBOARD ───
if st.session_state.current_page == "dashboard":
    st.title("Dashboard")
    total, active, interviews, offers, rate = job_stats()

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1: st.metric("Total Applied", total)
    with col2: st.metric("Active Pipeline", active)
    with col3: st.metric("Interviews", interviews)
    with col4: st.metric("Offers", offers)
    with col5: st.metric("Response Rate", rate)

    st.divider()
    col_l, col_r = st.columns([3, 2])

    with col_l:
        st.subheader("Recent Applications")
        recent = sorted(get_jobs(), key=lambda x: x.get("created_at", 0), reverse=True)[:6]
        if not recent:
            st.info("No applications yet. Add your first job in the tracker!")
        else:
            for j in recent:
                s = STATUSES[j["status"]]
                badge_color_map = {
                    "wishlist": "#7a7a8c", "applied": "#5bc8f5", "screen": "#f5c35b",
                    "interview": "#a55bf5", "offer": "#c5f135", "rejected": "#f55b7a"
                }
                col_a, col_b = st.columns([4, 1])
                with col_a:
                    st.markdown(f"""
                    <div class="job-card">
                        <div class="job-company">{j['company']}</div>
                        <div class="job-role">{j.get('role', '—')}</div>
                    </div>""", unsafe_allow_html=True)
                with col_b:
                    st.markdown(f"""<br><span class="badge badge-{j['status']}">{s['icon']} {s['label']}</span>""",
                               unsafe_allow_html=True)

        if st.button("View All →", key="dash_view_all"):
            st.session_state.current_page = "tracker"
            st.rerun()

    with col_r:
        st.subheader("🧭 Coach Insight")
        jobs = get_jobs()
        profile = st.session_state.profile

        if not profile.get("resume") or not jobs:
            st.info("Fill in your profile and add some job applications to get a personalized coach insight.")
        else:
            if st.button("Generate Insight", key="gen_insight"):
                jobs_summary = "\n".join([f"- {j['company']} ({j['role']}) — {STATUSES[j['status']]['label']}" for j in jobs])
                prompt = f"""Candidate: {profile['name'] or 'job seeker'}, targeting: {profile['role'] or 'tech roles'}
Job applications:
{jobs_summary}

Give ONE sharp, specific coach insight (3-4 sentences). Spot a pattern, risk, or opportunity. Be direct and specific. Reference actual companies/roles from their list."""

                with st.spinner("Analyzing your pipeline..."):
                    insight = call_claude([{"role": "user", "content": prompt}],
                                        "You are a top-tier career strategist. Be concise, specific, and actionable.")
                st.markdown(f"""
                <div style="background:#161720;border:1px solid rgba(197,241,53,0.2);border-radius:10px;padding:16px;font-size:13px;line-height:1.7;color:#eeedf0;">
                🧭 {insight}
                </div>""", unsafe_allow_html=True)

# ─── JOB TRACKER ───
elif st.session_state.current_page == "tracker":
    col_title, col_btn = st.columns([6, 1])
    with col_title:
        st.title("Job Tracker")
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("+ Add Job", key="add_job_top"):
            st.session_state.current_page = "add_job"
            st.session_state.editing_job_id = None
            st.rerun()

    # Kanban
    tabs = st.tabs([f"{STATUSES[s]['icon']} {STATUSES[s]['label']}" for s in STATUSES])
    for i, status_key in enumerate(STATUSES):
        with tabs[i]:
            status_jobs = [j for j in get_jobs() if j["status"] == status_key]
            s = STATUSES[status_key]
            st.markdown(f"**{len(status_jobs)} application{'s' if len(status_jobs) != 1 else ''}**")

            if not status_jobs:
                st.markdown(f"""<div style="border:1px dashed rgba(255,255,255,0.1);border-radius:10px;padding:24px;text-align:center;color:#555568;font-size:13px;">No applications here yet</div>""",
                           unsafe_allow_html=True)
            else:
                for j in status_jobs:
                    with st.container():
                        c1, c2, c3 = st.columns([5, 2, 1])
                        with c1:
                            st.markdown(f"**{j['company']}** — {j.get('role', '—')}")
                            if j.get('location'):
                                st.caption(f"📍 {j['location']}" + (f" · {j['salary']}" if j.get('salary') else ""))
                            if j.get('date'):
                                st.caption(f"Applied: {j['date']}")
                        with c2:
                            if j.get('tags'):
                                st.caption(" · ".join(j['tags'][:3]))
                        with c3:
                            if st.button("Edit", key=f"edit_{j['id']}"):
                                st.session_state.current_page = "add_job"
                                st.session_state.editing_job_id = j["id"]
                                st.rerun()
                        st.divider()

# ─── ADD / EDIT JOB ───
elif st.session_state.current_page == "add_job":
    editing_id = getattr(st.session_state, "editing_job_id", None)
    existing = get_job(editing_id) if editing_id else None

    st.title("Edit Job" if existing else "Add Job")

    tab1, tab2, tab3 = st.tabs(["📋 Details", "📈 Progress", "📄 Notes & JD"])

    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            company = st.text_input("Company *", value=existing.get("company", "") if existing else "")
            status = st.selectbox("Status", list(STATUSES.keys()),
                                  format_func=lambda x: f"{STATUSES[x]['icon']} {STATUSES[x]['label']}",
                                  index=list(STATUSES.keys()).index(existing.get("status", "applied")) if existing else 1)
            location = st.text_input("Location", value=existing.get("location", "") if existing else "")

        with col2:
            role = st.text_input("Role / Title", value=existing.get("role", "") if existing else "")
            applied_date = st.date_input("Date Applied",
                                         value=date.fromisoformat(existing["date"]) if existing and existing.get("date") else date.today())
            salary = st.text_input("Salary Range", value=existing.get("salary", "") if existing else "")

        job_url = st.text_input("Job URL", value=existing.get("url", "") if existing else "")
        tags_input = st.text_input("Tags (comma separated)", value=", ".join(existing.get("tags", [])) if existing else "")

        col_save, col_del, col_cancel = st.columns([2, 1, 1])
        with col_save:
            if st.button("💾 Save Job", use_container_width=True):
                if not company:
                    st.error("Company name is required.")
                else:
                    job_data = {
                        "company": company, "role": role,
                        "status": status, "date": applied_date.isoformat(),
                        "location": location, "salary": salary,
                        "url": job_url,
                        "tags": [t.strip() for t in tags_input.split(",") if t.strip()],
                        "jd": existing.get("jd", "") if existing else "",
                        "notes": existing.get("notes", "") if existing else "",
                        "progress": existing.get("progress", []) if existing else [],
                    }
                    if existing:
                        job_data["id"] = editing_id
                        job_data["created_at"] = existing.get("created_at", datetime.now().timestamp())
                        update_job(editing_id, job_data)
                        st.success("✓ Job updated!")
                    else:
                        add_job(job_data)
                        st.success("✓ Job added!")
                    st.session_state.current_page = "tracker"
                    st.rerun()

        with col_del:
            if existing and st.button("🗑 Delete", use_container_width=True):
                delete_job(editing_id)
                st.session_state.current_page = "tracker"
                st.rerun()

        with col_cancel:
            if st.button("Cancel", use_container_width=True):
                st.session_state.current_page = "tracker"
                st.rerun()

    with tab2:
        if not existing:
            st.info("Save the job first, then track progress here.")
        else:
            st.subheader("Progress Timeline")
            # Timeline display
            status_order = list(STATUSES.keys())
            current_idx = status_order.index(existing.get("status", "applied"))
            progress_notes = existing.get("progress", [])

            for i, sk in enumerate(status_order):
                s = STATUSES[sk]
                is_done = i < current_idx
                is_current = sk == existing.get("status")
                indicator = "✅" if is_done else ("🔵" if is_current else "⚪")

                stage_notes = [n for n in progress_notes if n.get("status") == sk]
                note_html = "".join([f'<div style="font-size:14px;color:#7a7a8c;margin-top:4px;">💬 {n["note"]} <span style="color:#555568">({n["date"]})</span></div>' for n in stage_notes])

                st.markdown(f"""<div style="display:flex;gap:12px;padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.04);">
                    <span style="font-size:16px">{indicator}</span>
                    <div>
                        <span style="font-size:14px;font-weight:600;color:{'#c5f135' if is_current else '#7a7a8c' if is_done else '#555568'}">{s['label']}</span>
                        {note_html}
                    </div>
                </div>""", unsafe_allow_html=True)

            st.divider()
            st.subheader("Add Progress Note")
            new_status = st.selectbox("Stage", list(STATUSES.keys()),
                                      format_func=lambda x: f"{STATUSES[x]['icon']} {STATUSES[x]['label']}",
                                      index=current_idx, key="prog_status")
            note_text = st.text_area("Note", placeholder="e.g. Great phone screen with hiring manager, mentioned focus on LLM infra...")
            if st.button("Add Note"):
                if note_text.strip():
                    prog = existing.get("progress", [])
                    prog.append({"status": new_status, "note": note_text.strip(), "date": date.today().isoformat()})
                    update_job(editing_id, {"status": new_status, "progress": prog})
                    st.success("Note added!")
                    st.rerun()

    with tab3:
        if not existing:
            st.info("Save the job first to add notes and JD.")
        else:
            jd_text = st.text_area("Job Description (paste here to power AI agents)",
                                   value=existing.get("jd", ""),
                                   height=250,
                                   placeholder="Paste the full job description...")
            notes_text = st.text_area("Personal Notes",
                                      value=existing.get("notes", ""),
                                      height=150,
                                      placeholder="Why you're interested, who referred you, interview impressions...")
            if st.button("Save Notes & JD"):
                update_job(editing_id, {"jd": jd_text, "notes": notes_text})
                st.success("Saved!")
                st.rerun()

# ─── AGENTS ───
elif st.session_state.current_page == "agents":
    agent_key = st.session_state.current_agent
    agent_meta = {
        "coach":     ("🧭", "Career Coach", "Monitors your pipeline · diagnoses blocks · builds strategy · holds you accountable"),
        "resume":    ("✏️", "Resume Reviewer", "10-sec scan test · bullet rewrites · ATS keywords · positioning strategy"),
        "gap":       ("🔍", "Gap Identifier", "Fit score · critical gaps · what to close before interviews"),
        "interview": ("🎤", "Interview Coach", "Role-specific questions · realistic pressure · rubric-based feedback"),
        "study":     ("📚", "Study Planner", "Must-know topics · best resources · output-first learning schedule"),
        "partner":   ("🤝", "Study Partner", "Output-first · Feynman method · WHY before HOW · mistake patterns"),
    }
    icon, name, subtitle = agent_meta[agent_key]
    is_prep_agent = agent_key in PREP_AGENTS

    p = st.session_state.profile
    jobs = get_jobs()
    jobs_with_jd = [j for j in jobs if j.get("jd")]

    # For prep agents: job selector + auto-default prep_job_id
    if is_prep_agent:
        if not jobs_with_jd:
            st.info("Add jobs and paste job descriptions in the **Job Tracker** (Notes & JD tab) to unlock Resume, Gap, Interview, and Study agents. Each job gets its own set of preparation agents.")
            st.stop()
        valid_prep_ids = [j["id"] for j in jobs_with_jd]
        if st.session_state.prep_job_id not in valid_prep_ids:
            st.session_state.prep_job_id = jobs_with_jd[0]["id"]
        prep_job = get_job(st.session_state.prep_job_id) or jobs_with_jd[0]
        job_options = [(j["id"], f"{j['company']} — {j['role']}") for j in jobs_with_jd]
        option_ids = [jid for jid, _ in job_options]
        option_labels = [lb for _, lb in job_options]
        curr_idx = option_ids.index(st.session_state.prep_job_id) if st.session_state.prep_job_id in option_ids else 0
        st.markdown(f"### {icon} {name}")
        chosen_label = st.selectbox(
            "**Preparing for**",
            options=option_labels,
            index=curr_idx,
            key="prep_job_select",
        )
        chosen_id = option_ids[option_labels.index(chosen_label)]
        if chosen_id != st.session_state.prep_job_id:
            st.session_state.prep_job_id = chosen_id
            st.rerun()
        st.caption(subtitle)
    else:
        st.markdown(f"## {icon} {name}")
        st.caption(subtitle)

    col_h, col_clear = st.columns([5, 1])
    with col_clear:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Clear chat"):
            if is_prep_agent and st.session_state.prep_job_id:
                _set_prep_messages(agent_key, st.session_state.prep_job_id, [])
            else:
                st.session_state.conversations[agent_key] = []
                db_save("conversations", st.session_state.conversations)
            st.rerun()

    # Context status bar
    has_resume = bool(p.get("resume"))
    has_jobs = len(jobs) > 0
    has_jd = len(jobs_with_jd) > 0
    ctx_parts = []
    ctx_parts.append(f"{'✅' if has_resume else '⚠️'} Resume {'set' if has_resume else 'missing — go to Profile'}")
    ctx_parts.append(f"{'✅' if has_jobs else '⚠️'} {len(jobs)} job{'s' if len(jobs) != 1 else ''} tracked")
    ctx_parts.append(f"{'✅' if has_jd else '⚠️'} {len(jobs_with_jd)} job{'s' if len(jobs_with_jd) != 1 else ''} with JD")

    st.markdown(f"""<div style="background:#0f1015;border:1px solid rgba(255,255,255,0.06);border-radius:8px;padding:8px 14px;font-family:'IBM Plex Mono',monospace;font-size:12px;color:#7a7a8c;margin-bottom:16px;">
    {"&nbsp;&nbsp;·&nbsp;&nbsp;".join(ctx_parts)}
    </div>""", unsafe_allow_html=True)

    if is_prep_agent:
        messages = _get_prep_messages(agent_key, st.session_state.prep_job_id)
        prep_job = get_job(st.session_state.prep_job_id)
    else:
        messages = st.session_state.conversations.get(agent_key, [])

    if not messages:
        # Starter chips
        starters = {
            "coach":     ["Analyze my job search", "What's my biggest bottleneck?", "Build me a 30-day plan", "Plan my week and block study time"],
            "resume":    ["Review my resume for my latest application", "Rewrite my weakest bullets", "What ATS keywords am I missing?", "Help me reposition for ML Engineer"],
            "gap":       ["Give me a fit score for my top target", "What are my critical gaps?", "What can I close before interviews?", "How competitive am I?"],
            "interview": ["Run a mock technical interview", "Ask me behavioral questions", "Practice 'tell me about yourself'", "Test my system design knowledge"],
            "study":     ["Build a study plan for my active applications", "What should I learn first?", "Create a 2-week prep schedule", "List must-know ML concepts"],
            "partner":   ["Explain transformers to me", "Quiz me on what I should know", "Teach me system design", "Help me understand RAG"],
        }
        st.markdown(f"""<div style="text-align:center;padding:40px 20px;">
        <div style="font-size:36px;margin-bottom:12px;">{icon}</div>
        <div style="font-size:16px;font-weight:600;margin-bottom:6px;">{name}</div>
        <div style="font-size:13px;color:#7a7a8c;margin-bottom:24px;">{subtitle}</div>
        </div>""", unsafe_allow_html=True)

        cols = st.columns(2)
        for i, s in enumerate(starters.get(agent_key, [])):
            with cols[i % 2]:
                if st.button(f"↗ {s}", key=f"starter_{i}", use_container_width=True):
                    if is_prep_agent:
                        msgs = _get_prep_messages(agent_key, st.session_state.prep_job_id)
                        msgs.append({"role": "user", "content": s})
                        _set_prep_messages(agent_key, st.session_state.prep_job_id, msgs)
                    else:
                        st.session_state.conversations[agent_key].append({"role": "user", "content": s})
                        db_save("conversations", st.session_state.conversations)
                    st.rerun()
    else:
        # Render messages
        for msg in messages:
            if msg["role"] == "user":
                st.markdown(f"""
                <div class="chat-label" style="text-align:right">YOU</div>
                <div class="chat-msg-user">{msg['content']}</div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-label agent-label">{icon} {name}</div>
                <div class="chat-msg-agent">{msg['content']}</div>
                """, unsafe_allow_html=True)

        # If last message is from user, generate response
        if messages and messages[-1]["role"] == "user":
            prep_job = get_job(st.session_state.prep_job_id) if is_prep_agent else None
            system = get_system_prompt(agent_key, job=prep_job)
            api_messages = [{"role": m["role"], "content": m["content"]} for m in messages]

            with st.spinner(f"{name} is thinking..."):
                if agent_key == "coach" and is_calendar_connected():
                    response = call_claude_with_tools(api_messages, system, CALENDAR_TOOLS)
                else:
                    response = call_claude(api_messages, system)
            if is_prep_agent:
                msgs = _get_prep_messages(agent_key, st.session_state.prep_job_id)
                msgs.append({"role": "assistant", "content": response})
                _set_prep_messages(agent_key, st.session_state.prep_job_id, msgs)
            else:
                st.session_state.conversations[agent_key].append({"role": "assistant", "content": response})
                db_save("conversations", st.session_state.conversations)
            st.rerun()

    # Input
    st.divider()
    with st.form(key=f"chat_form_{agent_key}", clear_on_submit=True):
        col_input, col_send = st.columns([6, 1])
        with col_input:
            user_input = st.text_input(
                "Message",
                placeholder=f"Ask {name}...",
                label_visibility="collapsed"
            )
        with col_send:
            submitted = st.form_submit_button("Send →", use_container_width=True)

        if submitted and user_input.strip():
            if is_prep_agent:
                msgs = _get_prep_messages(agent_key, st.session_state.prep_job_id)
                msgs.append({"role": "user", "content": user_input.strip()})
                _set_prep_messages(agent_key, st.session_state.prep_job_id, msgs)
            else:
                st.session_state.conversations[agent_key].append({"role": "user", "content": user_input.strip()})
                db_save("conversations", st.session_state.conversations)
            st.rerun()

# ─── PROFILE ───
elif st.session_state.current_page == "profile":
    st.title("My Profile")
    st.caption("Your profile powers all 6 AI agents. The more detail you provide, the better the coaching.")

    p = st.session_state.profile

    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Your Name", value=p.get("name", ""), placeholder="e.g. Annie Chen")
    with col2:
        target_role = st.text_input("Target Role", value=p.get("role", ""), placeholder="e.g. ML Engineer, Data Engineer, AI Researcher")

    resume = st.text_area(
        "Resume / Background (paste full text)",
        value=p.get("resume", ""),
        height=220,
        placeholder="Your work experience, education, skills, projects...\n\nThe more detail, the more personalized your coaching will be."
    )

    goals = st.text_area(
        "Goals & Current Situation",
        value=p.get("goals", ""),
        height=100,
        placeholder="e.g. Breaking into ML engineering from data analytics. Targeting FAANG in 6 months. Not sure if startup or big tech. Open to relocating..."
    )

    if st.button("💾 Save Profile", use_container_width=False):
        st.session_state.profile = {
            "name": name, "role": target_role,
            "resume": resume, "goals": goals
        }
        db_save("profile", st.session_state.profile)
        st.success("✓ Profile saved! Your agents are now fully personalized.")

    st.divider()
    st.subheader("📅 Google Calendar")
    st.caption("Connect your calendar so the Career Coach can plan your schedule — block study time, add interview prep, and suggest when to work on applications.")
    if is_calendar_connected():
        st.success("✓ Google Calendar connected. The Career Coach can view and create events.")
        if st.button("Disconnect Google Calendar", key="disconnect_cal"):
            disconnect_calendar()
            st.rerun()
    else:
        if st.button("Connect Google Calendar", key="connect_cal"):
            with st.spinner("Opening browser for Google sign-in..."):
                ok, msg = connect_calendar_oauth()
            if ok:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

    st.divider()
    st.subheader("Quick Tips")
    st.markdown("""
    **For best results:**
    - **Resume**: Paste your actual resume text (not formatted) — experience, education, projects, skills
    - **Goals**: What role, what timeline, what's your biggest uncertainty right now?
    - **Job Descriptions**: Paste JDs directly into each job in the tracker — this powers all 6 agents
    - **Study Partner & Planner**: Already know how you learn best — output-first, builder-strategist style is baked in
    """)
