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
with open(Path(__file__).parent / "styles.css") as _f:
    st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)

# ─── DORAEMON BUDDY WIDGET ───
# CSS + HTML via st.markdown (styles render fine; script tags are stripped by Streamlit/React)
st.markdown("""
<div id="doraemon-float">
  <div id="doraemon-bubble">✨ Hey Annie! I'm cheering you on~ 💙</div>
  <div id="doraemon-avatar" title="Drag me anywhere · Click for a surprise!">
    <svg width="88" height="108" viewBox="0 0 200 240" xmlns="http://www.w3.org/2000/svg">
      <ellipse cx="100" cy="228" rx="50" ry="9" fill="rgba(0,0,0,0.18)"/>
      <ellipse cx="100" cy="172" rx="68" ry="58" fill="#0099DD"/>
      <ellipse cx="100" cy="180" rx="46" ry="40" fill="white"/>
      <ellipse cx="100" cy="181" rx="32" ry="18" fill="#0d1020" stroke="rgba(0,153,221,0.3)" stroke-width="1.5"/>
      <path d="M68 181 Q100 167 132 181" stroke="rgba(0,153,221,0.3)" stroke-width="1.5" fill="none"/>
      <ellipse cx="72"  cy="222" rx="28" ry="14" fill="white"/>
      <ellipse cx="128" cy="222" rx="28" ry="14" fill="white"/>
      <ellipse cx="38"  cy="172" rx="16" ry="10" fill="#0099DD" transform="rotate(-20 38 172)"/>
      <circle  cx="24"  cy="182" r="14" fill="white"/>
      <ellipse cx="162" cy="172" rx="16" ry="10" fill="#0099DD" transform="rotate(20 162 172)"/>
      <circle  cx="176" cy="182" r="14" fill="white"/>
      <g class="dora-tail">
        <path d="M148 200 Q168 195 172 210 Q170 222 158 218" stroke="#0099DD" stroke-width="8" fill="none" stroke-linecap="round"/>
        <circle cx="160" cy="218" r="8" fill="#0099DD"/>
        <circle cx="160" cy="218" r="4" fill="white"/>
      </g>
      <circle cx="100" cy="96"  r="72" fill="#0099DD"/>
      <ellipse cx="100" cy="108" rx="54" ry="46" fill="white"/>
      <ellipse cx="60"  cy="116" rx="16" ry="10" fill="#ff6666" opacity="0.55"/>
      <ellipse cx="140" cy="116" rx="16" ry="10" fill="#ff6666" opacity="0.55"/>
      <circle cx="78"  cy="88" r="16" fill="white" class="dora-eye"/>
      <circle cx="82"  cy="90" r="9"  fill="#111"/>
      <circle cx="85"  cy="87" r="3.5" fill="white"/>
      <circle cx="122" cy="88" r="16" fill="white" class="dora-eye"/>
      <circle cx="118" cy="90" r="9"  fill="#111"/>
      <circle cx="121" cy="87" r="3.5" fill="white"/>
      <circle cx="100" cy="104" r="9" fill="#cc2222"/>
      <ellipse cx="97" cy="101" rx="3" ry="2" fill="white" opacity="0.85"/>
      <line x1="100" y1="113" x2="100" y2="128" stroke="#aaa" stroke-width="2"/>
      <path id="dora-mouth" d="M72 128 Q100 150 128 128" stroke="#aaa" stroke-width="2.5" fill="none" stroke-linecap="round"/>
      <line x1="30"  y1="108" x2="88"  y2="114" stroke="#666" stroke-width="1.5" stroke-linecap="round"/>
      <line x1="28"  y1="120" x2="88"  y2="120" stroke="#666" stroke-width="1.5" stroke-linecap="round"/>
      <line x1="30"  y1="132" x2="88"  y2="126" stroke="#666" stroke-width="1.5" stroke-linecap="round"/>
      <line x1="170" y1="108" x2="112" y2="114" stroke="#666" stroke-width="1.5" stroke-linecap="round"/>
      <line x1="172" y1="120" x2="112" y2="120" stroke="#666" stroke-width="1.5" stroke-linecap="round"/>
      <line x1="170" y1="132" x2="112" y2="126" stroke="#666" stroke-width="1.5" stroke-linecap="round"/>
      <rect x="50" y="140" width="100" height="16" rx="8" fill="#cc2222"/>
      <circle cx="100" cy="154" r="10" fill="#FFCC00"/>
      <circle cx="100" cy="157" r="3"  fill="#aa8800"/>
      <line x1="91" y1="154" x2="109" y2="154" stroke="#aa8800" stroke-width="1.5"/>
      <circle cx="96" cy="150" r="2.5" fill="white" opacity="0" class="dora-bell"/>
    </svg>
  </div>
</div>
""", unsafe_allow_html=True)

# JavaScript is injected via components.html() which runs in an iframe on the same origin,
# allowing window.parent access — this is the correct way to run JS in Streamlit.
import streamlit.components.v1 as _st_components
_st_components.html("""
<script>
(function() {
  var pd = window.parent.document;

  var MSGS = [
    "You're doing amazing~ 💙 Keep it up!",
    "I believe in you, Annie! 🌟",
    "One step at a time~ I'm with you! ✨",
    "Every application gets you closer! 🎯",
    "You've totally got this! 💪💙",
    "Stay curious — that's your superpower! 🔧",
    "Dream big, grind smart~ 🚀",
    "I'd give you a gadget, but you're already amazing! 🎒",
    "Proud of you for showing up today! 🌟",
    "Your offer is coming~ just keep going! 💙",
    "Rest when you need to — I'll still be here! 🌙",
    "Small wins count! Celebrate every step~ 🎉",
    "You showed up today. That already matters! 💫",
  ];

  var AUTO_MSGS = [
    "✨ Hey Annie! Cheering you on~ 💙",
    "💙 You're making progress — keep going!",
    "🌟 Today's effort = tomorrow's offer!",
    "🎯 Focus mode: activated! You've got this~",
    "💫 I'm right here with you, always!",
    "🔵 Every rejection is just a redirect~ 💙",
  ];

  var EMOJIS = ['💙','⭐','✨','💫','🌟','🎯','💪'];

  function init() {
    var floatEl = pd.getElementById('doraemon-float');
    var avatar  = pd.getElementById('doraemon-avatar');
    var bubble  = pd.getElementById('doraemon-bubble');
    var mouth   = pd.getElementById('dora-mouth');

    if (!floatEl || !avatar || !bubble) { setTimeout(init, 120); return; }
    if (avatar.dataset.doraReady) return;   // prevent double-init on re-render
    avatar.dataset.doraReady = '1';

    /* ── Drag state ── */
    var dragging = false, moved = false;
    var startMouseX, startMouseY, startLeft, startBottom;

    avatar.addEventListener('mousedown', function(e) {
      if (e.button !== 0) return;
      dragging = true; moved = false;
      startMouseX = e.clientX; startMouseY = e.clientY;
      var rect = floatEl.getBoundingClientRect();
      startLeft   = rect.left;
      startBottom = window.parent.innerHeight - rect.bottom;
      avatar.classList.add('dora-dragging');
      e.preventDefault();
    });

    pd.addEventListener('mousemove', function(e) {
      if (!dragging) return;
      var dx = e.clientX - startMouseX;
      var dy = e.clientY - startMouseY;
      if (Math.abs(dx) > 4 || Math.abs(dy) > 4) moved = true;
      var newLeft   = Math.max(0, Math.min(window.parent.innerWidth  - 96,  startLeft   + dx));
      var newBottom = Math.max(0, Math.min(window.parent.innerHeight - 120, startBottom - dy));
      floatEl.style.right  = 'auto';
      floatEl.style.left   = newLeft   + 'px';
      floatEl.style.bottom = newBottom + 'px';
    });

    pd.addEventListener('mouseup', function(e) {
      if (!dragging) return;
      dragging = false;
      avatar.classList.remove('dora-dragging');
      if (!moved) tap(e);   // treat no-move mousedown+up as click
    });

    /* ── Touch drag ── */
    avatar.addEventListener('touchstart', function(e) {
      var t = e.touches[0];
      dragging = true; moved = false;
      startMouseX = t.clientX; startMouseY = t.clientY;
      var rect = floatEl.getBoundingClientRect();
      startLeft   = rect.left;
      startBottom = window.parent.innerHeight - rect.bottom;
    }, {passive: true});

    pd.addEventListener('touchmove', function(e) {
      if (!dragging) return;
      var t = e.touches[0];
      var dx = t.clientX - startMouseX;
      var dy = t.clientY - startMouseY;
      moved = true;
      var newLeft   = Math.max(0, Math.min(window.parent.innerWidth  - 96,  startLeft   + dx));
      var newBottom = Math.max(0, Math.min(window.parent.innerHeight - 120, startBottom - dy));
      floatEl.style.right  = 'auto';
      floatEl.style.left   = newLeft   + 'px';
      floatEl.style.bottom = newBottom + 'px';
    }, {passive: true});

    pd.addEventListener('touchend', function(e) {
      if (!dragging) return;
      dragging = false;
      if (!moved) {
        var t = e.changedTouches[0];
        tap({clientX: t.clientX, clientY: t.clientY});
      }
    });

    /* ── Tap / click ── */
    var lastMsgIdx = -1, hideTimer = null;

    function tap(e) {
      // Pick a new random message
      var idx;
      do { idx = Math.floor(Math.random() * MSGS.length); } while (idx === lastMsgIdx);
      lastMsgIdx = idx;

      // Show bubble
      bubble.classList.remove('dora-hidden');
      bubble.innerHTML = MSGS[idx];
      clearTimeout(hideTimer);
      hideTimer = setTimeout(function(){ bubble.classList.add('dora-hidden'); }, 5500);

      // Bounce animation on avatar
      avatar.classList.remove('dora-bounce');
      void avatar.offsetWidth;            // reflow to restart animation
      avatar.classList.add('dora-bounce');
      setTimeout(function(){ avatar.classList.remove('dora-bounce'); }, 400);

      // Widen smile briefly
      if (mouth) {
        mouth.setAttribute('d', 'M66 128 Q100 158 134 128');
        setTimeout(function(){ mouth.setAttribute('d', 'M72 128 Q100 150 128 128'); }, 600);
      }

      // Burst of particles
      var rect = floatEl.getBoundingClientRect();
      var cx = rect.left + rect.width  / 2;
      var cy = rect.top  + rect.height / 2;
      for (var i = 0; i < 6; i++) {
        (function(i){
          setTimeout(function(){
            var el = pd.createElement('div');
            el.className = 'dora-particle';
            el.textContent = EMOJIS[Math.floor(Math.random() * EMOJIS.length)];
            el.style.left = (cx + (Math.random()-0.5)*70) + 'px';
            el.style.top  = (cy + (Math.random()-0.5)*50) + 'px';
            pd.body.appendChild(el);
            setTimeout(function(){ el.remove(); }, 1200);
          }, i * 60);
        })(i);
      }
    }

    /* ── Auto-rotate idle messages every 14s ── */
    var autoIdx = 0;
    setInterval(function(){
      autoIdx = (autoIdx + 1) % AUTO_MSGS.length;
      bubble.classList.remove('dora-hidden');
      bubble.innerHTML = AUTO_MSGS[autoIdx];
      clearTimeout(hideTimer);
      hideTimer = setTimeout(function(){ bubble.classList.add('dora-hidden'); }, 6000);
    }, 14000);
  }

  init();
})();
</script>
""", height=0)

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

# ─── PROJECTS DATABASE ───
def _projects_db():
    con = sqlite3.connect(str(DB_PATH))
    con.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            title         TEXT    NOT NULL,
            source_type   TEXT    NOT NULL,
            raw_content   TEXT    NOT NULL,
            technologies  TEXT    DEFAULT '[]',
            metrics       TEXT    DEFAULT '[]',
            contributions TEXT    DEFAULT '',
            challenges    TEXT    DEFAULT '',
            summary       TEXT    DEFAULT '',
            created_at    REAL    NOT NULL
        )
    """)
    con.commit()
    return con

def db_save_project(title: str, source_type: str, raw_content: str, extracted: dict) -> int:
    con = _projects_db()
    cur = con.execute(
        """INSERT INTO projects
           (title, source_type, raw_content, technologies, metrics, contributions, challenges, summary, created_at)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (
            title, source_type, raw_content[:60000],
            json.dumps(extracted.get("technologies", []), ensure_ascii=False),
            json.dumps(extracted.get("metrics", []), ensure_ascii=False),
            extracted.get("contributions", ""),
            extracted.get("challenges", ""),
            extracted.get("summary", ""),
            datetime.now().timestamp(),
        )
    )
    pid = cur.lastrowid
    con.commit()
    con.close()
    return pid

def db_get_projects() -> list:
    try:
        con = _projects_db()
        rows = con.execute(
            "SELECT id, title, source_type, technologies, metrics, contributions, challenges, summary, created_at "
            "FROM projects ORDER BY created_at DESC"
        ).fetchall()
        con.close()
        return [
            {
                "id": r[0], "title": r[1], "source_type": r[2],
                "technologies": json.loads(r[3] or "[]"),
                "metrics":      json.loads(r[4] or "[]"),
                "contributions": r[5] or "",
                "challenges":    r[6] or "",
                "summary":       r[7] or "",
                "created_at":    r[8],
            }
            for r in rows
        ]
    except Exception:
        return []

def db_delete_project(project_id: int) -> None:
    con = _projects_db()
    con.execute("DELETE FROM projects WHERE id=?", (project_id,))
    con.commit()
    con.close()

def read_pdf_bytes(file_bytes: bytes) -> str:
    """Extract text from PDF bytes using pypdf."""
    import io as _io
    try:
        import pypdf
        reader = pypdf.PdfReader(_io.BytesIO(file_bytes))
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text and text.strip():
                pages.append(text.strip())
        return "\n\n".join(pages)
    except Exception as e:
        return f"[PDF extraction error: {e}]"

def read_docx_bytes(file_bytes: bytes) -> str:
    """Extract text from a .docx file.
    Primary: python-docx. Fallback: stdlib zipfile + XML (no extra deps required).
    """
    import io as _io

    # ── Primary: python-docx ──
    try:
        import docx as _docx
        doc = _docx.Document(_io.BytesIO(file_bytes))
        parts = []
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                parts.append(text)
        for table in doc.tables:
            for row in table.rows:
                row_text = "  |  ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                if row_text:
                    parts.append(row_text)
        if parts:
            return "\n\n".join(parts)
    except Exception:
        pass

    # ── Fallback: pure stdlib ZIP + XML parse ──
    try:
        import zipfile as _zf
        import xml.etree.ElementTree as _ET

        W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

        with _zf.ZipFile(_io.BytesIO(file_bytes)) as z:
            with z.open("word/document.xml") as f:
                tree = _ET.parse(f)

        root = tree.getroot()
        paragraphs = []
        for para in root.iter(f"{{{W}}}p"):
            runs = [node.text for node in para.iter(f"{{{W}}}t") if node.text]
            line = "".join(runs).strip()
            if line:
                paragraphs.append(line)

        if paragraphs:
            return "\n\n".join(paragraphs)
        return "[DOCX appears to have no readable text content]"
    except Exception as e:
        return f"[DOCX extraction error: {e}]"

def extract_project_with_claude(raw_text: str, title_hint: str = "") -> dict:
    """Call Claude Haiku to extract structured project data. Only uses facts present in the text."""
    import re as _re
    client = get_client()
    if not client or client == "invalid_format":
        return {
            "title": title_hint or "Untitled Project",
            "technologies": [], "metrics": [],
            "contributions": raw_text[:400],
            "challenges": "", "summary": raw_text[:200],
        }
    prompt = f"""You are extracting structured facts from a project report or description.
Extract ONLY what is explicitly stated — never invent or infer metrics or details not present in the text.

PROJECT TITLE HINT: {title_hint or "(infer from content)"}

PROJECT CONTENT:
{raw_text[:8000]}

Return a JSON object with EXACTLY these keys:
{{
  "title": "project title (inferred or confirmed)",
  "technologies": ["each specific tool / language / framework / library / platform explicitly mentioned"],
  "metrics": ["copy exact numbers/percentages/scale from the text only — empty array if none"],
  "contributions": "2-4 sentences on what this person specifically built, owned, or led (first-person perspective, past tense)",
  "challenges": "1-3 sentences on key technical problems solved or design decisions made",
  "summary": "2-sentence summary optimized for matching against job descriptions"
}}

STRICT RULES:
- metrics: only include figures EXPLICITLY in the text. If none exist, return [].
- Never add facts not in the source text.
- Return ONLY valid JSON. No markdown fences, no other text."""
    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=900,
            messages=[{"role": "user", "content": prompt}]
        )
        text = _extract_text_blocks(response.content)
        match = _re.search(r'\{.*\}', text, _re.DOTALL)
        if match:
            data = json.loads(match.group())
            if "title" in data:
                return data
    except Exception:
        pass
    return {
        "title": title_hint or "Untitled Project",
        "technologies": [], "metrics": [],
        "contributions": raw_text[:400],
        "challenges": "", "summary": raw_text[:200],
    }

def build_project_context_for_resume() -> str:
    """Format all saved projects into a context block for the Resume Reviewer prompt."""
    projects = db_get_projects()
    if not projects:
        return ""
    lines = [
        "━━━ PROJECT LIBRARY — Annie's Verified Work (ground truth — use these facts, never hallucinate) ━━━",
        "INSTRUCTION: When rewriting or evaluating resume bullets, pull relevant details from the projects below.",
        "Auto-match: identify which project(s) best align with the JD requirements, then use their facts.",
        "If a metric or technology is NOT in this library, do NOT invent it — use [X%] / [N users] placeholders.\n",
    ]
    for proj in projects:
        lines.append(f"▸ PROJECT: {proj['title']}")
        if proj["technologies"]:
            lines.append(f"  Technologies : {', '.join(proj['technologies'])}")
        if proj["metrics"]:
            lines.append(f"  Metrics      : {' | '.join(proj['metrics'])}")
        if proj["contributions"]:
            lines.append(f"  Contributions: {proj['contributions']}")
        if proj["challenges"]:
            lines.append(f"  Challenges   : {proj['challenges']}")
        if proj["summary"]:
            lines.append(f"  Summary      : {proj['summary']}")
        lines.append("")
    lines.append("━━━ END PROJECT LIBRARY ━━━")
    return "\n".join(lines)


# Per-job agents: Resume, Gap, Interview, Study are keyed by job_id. Coach & Partner are global.
PREP_AGENTS = ("resume", "gap", "interview", "study")
GLOBAL_AGENTS = ("coach", "partner", "synthesizer", "outreach")

def _migrate_conversations(raw: dict, jobs: list) -> dict:
    """Migrate old flat format to per-job format. Coach & Partner stay as lists."""
    out = {}
    out["coach"] = raw.get("coach", []) if isinstance(raw.get("coach"), list) else []
    out["partner"] = raw.get("partner", []) if isinstance(raw.get("partner"), list) else []
    out["synthesizer"] = raw.get("synthesizer", []) if isinstance(raw.get("synthesizer"), list) else []
    out["outreach"] = raw.get("outreach", []) if isinstance(raw.get("outreach"), list) else []

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
            "name": "", "role": "", "resume": "", "goals": "",
            "university": "", "gpa": "", "graduation": "",
            "resume_constraints": ""
        })
        # Back-fill new fields for existing saved profiles
        for _f in ("university", "gpa", "graduation", "resume_constraints"):
            if _f not in st.session_state.profile:
                st.session_state.profile[_f] = ""
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

AGENT_TOOLS = [
    {
        "name": "run_gap_analysis",
        "description": "Run a full gap analysis for a specific job — fit score, critical gaps, closeable gaps, action plan. Use when user asks how well they match a role, whether to apply, or what gaps to close.",
        "input_schema": {
            "type": "object",
            "properties": {
                "job_id": {"type": "integer", "description": "Numeric job ID from the tracker (shown as [ID:N])."},
                "question": {"type": "string", "description": "Optional: specific focus (e.g. 'focus on the ML gap')."},
            },
            "required": ["job_id"],
        },
    },
    {
        "name": "run_resume_review",
        "description": "Rewrite and optimize resume bullets for a specific job — keyword alignment, ATS, copy-paste ready output. Use when user wants to tailor their resume to a role.",
        "input_schema": {
            "type": "object",
            "properties": {
                "job_id": {"type": "integer", "description": "Numeric job ID from the tracker."},
                "instruction": {"type": "string", "description": "Optional: e.g. 'show full analysis', 'rewrite projects only'."},
            },
            "required": ["job_id"],
        },
    },
    {
        "name": "draft_outreach",
        "description": "Draft a LinkedIn DM, connection request, referral ask, cold email, or follow-up for a target company. Use when user wants to reach out to someone.",
        "input_schema": {
            "type": "object",
            "properties": {
                "company": {"type": "string", "description": "Target company name."},
                "message_type": {
                    "type": "string",
                    "enum": ["linkedin_connection", "linkedin_dm", "referral_request", "cold_email", "follow_up"],
                    "description": "Type of outreach message.",
                },
                "contact_name": {"type": "string", "description": "Optional: name/role of the recipient."},
                "context": {"type": "string", "description": "Optional: how they found this person, shared connections, role to reference."},
            },
            "required": ["company", "message_type"],
        },
    },
    {
        "name": "run_interview_prep",
        "description": "Run mock interview or interview prep for a specific job. Use when user wants practice questions or prep for an upcoming interview.",
        "input_schema": {
            "type": "object",
            "properties": {
                "job_id": {"type": "integer", "description": "Numeric job ID from the tracker."},
                "focus": {"type": "string", "description": "Optional: 'behavioral', 'technical', 'system design', 'full round'."},
            },
            "required": ["job_id"],
        },
    },
    {
        "name": "run_study_plan",
        "description": "Build a prioritized study plan for a specific job or across all active applications. Use when user asks what to study or wants a prep schedule.",
        "input_schema": {
            "type": "object",
            "properties": {
                "job_id": {"type": "integer", "description": "Optional: job ID for a role-specific plan. Omit for cross-application plan."},
                "focus": {"type": "string", "description": "Optional: e.g. '2-week timeline', 'ML fundamentals only'."},
            },
            "required": [],
        },
    },
    {
        "name": "synthesize_resume",
        "description": "Analyze patterns across all tracked JDs and produce optimized multi-company resume versions. Use when user wants generalized resume strategy across multiple targets.",
        "input_schema": {
            "type": "object",
            "properties": {
                "instruction": {"type": "string", "description": "Optional: e.g. 'focus on ML/DS roles', 'what skills appear most'."},
            },
            "required": [],
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

def _run_agent_tool(name: str, input_data: dict) -> str:
    """Dispatch a coach tool call to the appropriate sub-agent."""
    SUB_AGENT_MAX_TOKENS = 2000

    if name == "run_gap_analysis":
        job = get_job(input_data.get("job_id"))
        if not job:
            return f"Error: No job found with ID {input_data.get('job_id')}. Check tracker for valid IDs."
        q = input_data.get("question", "")
        msg = f"Run a full gap analysis for {job['company']} — {job['role']}." + (f" Focus: {q}" if q else "")
        return call_claude([{"role": "user", "content": msg}], get_system_prompt("gap", job=job), max_tokens=SUB_AGENT_MAX_TOKENS)

    elif name == "run_resume_review":
        job = get_job(input_data.get("job_id"))
        if not job:
            return f"Error: No job found with ID {input_data.get('job_id')}."
        ins = input_data.get("instruction", "")
        msg = f"Review and rewrite the resume for {job['company']} — {job['role']}." + (f" {ins}" if ins else "")
        return call_claude([{"role": "user", "content": msg}], get_system_prompt("resume", job=job), max_tokens=SUB_AGENT_MAX_TOKENS)

    elif name == "draft_outreach":
        company = input_data.get("company", "")
        mtype = input_data.get("message_type", "linkedin_dm").replace("_", " ")
        contact = input_data.get("contact_name", "")
        ctx = input_data.get("context", "")
        msg = f"Draft a {mtype} to {contact or 'someone'} at {company}." + (f" Context: {ctx}" if ctx else "")
        return call_claude([{"role": "user", "content": msg}], get_system_prompt("outreach"), max_tokens=SUB_AGENT_MAX_TOKENS)

    elif name == "run_interview_prep":
        job = get_job(input_data.get("job_id"))
        if not job:
            return f"Error: No job found with ID {input_data.get('job_id')}."
        focus = input_data.get("focus", "")
        msg = f"Run interview prep for {job['company']} — {job['role']}." + (f" Focus: {focus}" if focus else " Start with the most likely question types.")
        return call_claude([{"role": "user", "content": msg}], get_system_prompt("interview", job=job), max_tokens=SUB_AGENT_MAX_TOKENS)

    elif name == "run_study_plan":
        job_id = input_data.get("job_id")
        job = get_job(job_id) if job_id else None
        focus = input_data.get("focus", "")
        msg = (f"Build a study plan for {job['company']} — {job['role']}." if job else "Build a study plan across all my active applications.") + (f" Focus: {focus}" if focus else "")
        return call_claude([{"role": "user", "content": msg}], get_system_prompt("study", job=job), max_tokens=SUB_AGENT_MAX_TOKENS)

    elif name == "synthesize_resume":
        ins = input_data.get("instruction", "")
        msg = "Analyze patterns across all tracked JDs and produce optimized resume versions." + (f" {ins}" if ins else "")
        return call_claude([{"role": "user", "content": msg}], get_system_prompt("synthesizer"), max_tokens=SUB_AGENT_MAX_TOKENS)

    return f"Unknown agent tool: {name}"


def _run_tool(name: str, input_data: dict) -> str:
    """Route tool calls to calendar tools or agent tools."""
    if name in {t["name"] for t in CALENDAR_TOOLS}:
        return _run_calendar_tool(name, input_data)
    return _run_agent_tool(name, input_data)


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
                result = _run_tool(block.name, block.input)
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

    # Build internship context block used across all agents
    intern_ctx_parts = []
    if p.get("university"):
        intern_ctx_parts.append(f"University: {p['university']}")
    if p.get("graduation"):
        intern_ctx_parts.append(f"Graduation: {p['graduation']}")
    if p.get("gpa"):
        intern_ctx_parts.append(f"GPA: {p['gpa']}")
    intern_ctx = "\n".join(intern_ctx_parts) if intern_ctx_parts else ""

    jobs_summary = "\n".join([
        f"- [ID:{j['id']}] {j['company']} | {j['role']} | {STATUSES[j['status']]['label']} | Applied: {j.get('date', 'unknown')}"
        + (f" | Deadline: {j['deadline']}" if j.get('deadline') else "")
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
        base = f"""You are Annie's personal internship career strategist. You combine the sharpness of a McKinsey advisor with the directness of a senior tech recruiter who has seen thousands of intern applications. You know exactly what moves the needle and what doesn't.

ANNIE'S PROFILE:
Name: {p['name'] or 'Annie'}
Target Role: {p['role'] or 'Not specified — ask before advising'}
{intern_ctx}
Background:
{p['resume'] or '⚠️ No resume set — ask Annie to fill in her Profile before you can give personalized advice'}
Goals: {p['goals'] or 'Not specified'}

LIVE APPLICATION TRACKER:
{jobs_summary}

INTERNSHIP CONTEXT (always apply):
- Annie is a student hunting internships, not a full-time hire. Calibrate everything here.
- Intern cycles have hard close dates. Summer 2025/2026 roles at FAANG often close Oct–Nov. Urgency is real.
- GPA and school prestige matter more now than they will after her first job. Use them as assets.
- One referral can 10x resume review odds. Outreach to alumni and target-company employees is almost always the highest-ROI action.
- The goal isn't just any internship — it's one that could convert to a return offer or a strong brand name.
- Deadlines in tracker flagged within 14 days = treat as urgent. Name them explicitly.

HOW YOU THINK AND RESPOND:

**Read the tracker before anything else.** When Annie asks about strategy, scan the live data first:
- Volume: how many applications? Is the pipeline thin or healthy?
- Distribution: which stages? Lots of "Applied" with no "Screen" = resume or targeting problem. Lots of "Screen" with no "Interview" = phone screen problem. Interviews but no offers = closing problem.
- Concentration: too many applications to one company type = risk. Too broad = no clear positioning.
- Staleness: applications with no update in 3+ weeks need a follow-up or a status decision.
- Deadlines: are any approaching in the next 14 days? Name them.

**Be direct, not diplomatic.** If Annie's strategy has a flaw, name it plainly. She needs truth, not validation.

**Match the energy of the question:**
- Quick tactical question ("should I apply to X?") → short, direct answer + one consideration she might have missed
- Strategic question ("what should I focus on this month?") → diagnosis first, then 2–3 concrete options with trade-offs named
- Emotional question ("I feel like nothing is working") → acknowledge briefly, then reframe with data from the tracker

**Every substantive response ends with a next step.** One concrete action, with a timeline (today / this week). Not a list of 5 things — one thing, clearly stated.

**One clarifying question maximum per turn.** If you need more info, ask the single most important question. Don't interrogate.

**Name trade-offs explicitly:** "This gets you faster results but at the cost of X" — never recommend without acknowledging the cost.

TACTICAL KNOWLEDGE (use when relevant):
- Referral > Cold apply: a referral from any employee (not just friend) meaningfully improves odds
- LinkedIn recruiter messages: respond within 24 hours, always
- Application timing: applying within 3 days of posting increases response rate significantly
- Follow-up: one polite follow-up email 5–7 days after applying is standard practice, not annoying
- Intern interviews: behavioral questions expect project/coursework answers, not "I managed a team"
- Return offer leverage: one strong internship brand name unlocks the next — sequence matters"""
        base += """

TOOLS AVAILABLE — use these to act on Annie's behalf:

You have access to specialized sub-agents. Call them proactively when user intent clearly maps to one. Do NOT call a tool unless the user has expressed a relevant need — don't run analyses speculatively.

Before calling any tool:
- Tell Annie what you're about to do in one sentence: "Let me run a gap analysis for that role — one moment."
- Use the [ID:N] from the tracker to look up the correct job_id.

After receiving a tool result:
- Do NOT paste the raw output verbatim. Synthesize it.
- Lead with the single most important finding. Add your own strategic context.
- Connect it back to what Annie asked. Close with the next action.

WHEN TO CALL EACH TOOL:

run_gap_analysis(job_id, question?)
→ User asks: fit assessment, "should I apply", what gaps exist, how competitive they are for a role.
→ Pass the [ID:N] of the specific job. Add a `question` if they want a narrow focus.

run_resume_review(job_id, instruction?)
→ User asks: tailor resume for a role, get copy-paste bullets, keyword alignment for a specific application.
→ Pass `instruction="show full analysis"` only if user explicitly asks for the breakdown.

draft_outreach(company, message_type, contact_name?, context?)
→ User asks: write a LinkedIn message, cold DM, referral request, or follow-up for any company.
→ Choose message_type from: linkedin_connection, linkedin_dm, referral_request, cold_email, follow_up.

run_interview_prep(job_id, focus?)
→ User asks: mock interview, practice questions, interview prep for a role in the tracker.
→ Use `focus` to narrow to behavioral/technical/system design if specified.

run_study_plan(job_id?, focus?)
→ User asks: what to study, build a prep plan, must-know topics.
→ Omit job_id for a cross-application plan. Pass job_id for a role-specific plan.

synthesize_resume(instruction?)
→ User asks: resume patterns across companies, generalized resume strategy, multi-company resume versions.
→ Only useful once Annie has 2+ jobs with JDs in the tracker."""
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
        project_ctx = build_project_context_for_resume()
        constraints = p.get("resume_constraints") or "Not set — ask Annie once at the start of the session: 'How many work experiences, projects, and pages does your resume have?' then respect her answer."
        return f"""ABSOLUTE FORMATTING RULES — NON-NEGOTIABLE. THESE OVERRIDE ALL OTHER INSTINCTS:
1. Bullet character: ONLY "•". NEVER "-", "–", "—", "*", or any dash or asterisk variant. This is a hard constraint with zero exceptions.
2. No semicolons in any bullet or skills line. Use commas or split into separate bullets.
3. Default mode produces NO analysis headers, NO section labels like "Keyword Gap:", "ATS Report:", "Step 1:", "Diagnosis:", or "Review Process:". Only rewritten content.
4. Metric estimates: when a bullet lacks a number, YOU propose a specific estimate — format "~X%" or "~N [unit]" with one parenthetical sentence of rationale. NEVER write [X%] as a passive placeholder. NEVER ask Annie to estimate first — you propose, then she corrects if needed.
5. Space constraints below are hard limits. Never suggest bullets, sections, or content beyond them.

DEFAULT RESPONSE MODE — applies to every message UNLESS Annie says "show full analysis":
Output ONLY the following, nothing else:
  • Rewritten bullet points, preceded by a plain section label (Work Experience / Projects / Skills)
  • A rewritten Skills line if the JD requires changes
  • One final line: "Assumed: [list any ~estimates you made] — adjust if needed"

DO NOT output: keyword tables, ATS scores, fit scores, diagnosis paragraphs, numbered step headers, "Before → After" labels, or any prose analysis. Just the bullets, ready to paste.

To trigger full analysis mode, Annie must say: "show full analysis"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

You are a senior tech recruiter and resume coach who has reviewed thousands of intern applications at top companies (Google, Meta, Stripe, Anthropic, Jane Street, Citadel, Goldman, and top startups). Your one job: produce copy-paste-ready bullets that maximize Annie's interview callback rate for the specific role below.

ANNIE'S PROFILE:
{p['resume'] or '⚠️ Resume not provided. Ask Annie to paste her resume text before proceeding — you cannot give useful output without it.'}
{intern_ctx}

SPACE CONSTRAINTS (hard limits — never exceed):
{constraints}

TARGET ROLE: {recent_company} — {recent_role}
JOB DESCRIPTION:
{recent_jd}

{project_ctx if project_ctx else "⚠️  Project Library is empty. When rewriting bullets, note any facts you're inferring so Annie can verify. Remind her once that 📚 Project Library enables more accurate rewrites."}

INTERN RESUME STRUCTURE RULES:
• Education section FIRST. Include: school, degree, GPA (if ≥3.5/4.0 or ≥4.0/5.0), expected graduation. Relevant coursework only if directly named in the JD.
• GPA = {p.get('gpa') or 'not set'}. If strong (≥3.5/4.0 or ≥4.0/5.0), surface it. If weak or not set, omit silently.
• Work experience leads if Annie has prior internship experience. Projects lead otherwise.
• Enforce the space constraints above — if the constraints say 3 projects, produce exactly 3 sets of bullets. Do not suggest expanding.

BULLET QUALITY BAR (internalize this scale):
• 9/10: "Built real-time fraud detection pipeline with XGBoost on 550K daily transactions, cutting false positive rate from 2.1% to 0.6% (~$180K/year in avoided manual review costs)"
• 6/10: "Developed fraud detection model with XGBoost, improving accuracy by 15%"
• 3/10: "Built a fraud detection model using machine learning"
• 0/10: "Worked on fraud detection project"

Every rewritten bullet must reach at least 7/10. Bullet formula: [Strong verb] + [what] + [how / tech] + [outcome with number].

SIGNAL RULES:
• Strong: "built", "led", "designed", "deployed", "reduced", "increased", specific tech names, real numbers
• Weak: "assisted", "helped with", "familiar with", "worked on", "participated in", "contributed to"
• Never frame Annie as a helper or a participant. She owned things. Use that framing.

METRIC ESTIMATION RULES:
When a bullet has no number, propose one using context clues (dataset size, project scope, typical industry benchmarks). Format: ~X% or ~N [unit]. Add a brief parenthetical: "(estimated from [reasoning])". List all estimates in the "Assumed:" line at the end so Annie can confirm or correct.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FULL ANALYSIS MODE — only runs when Annie says "show full analysis":

Step 1 — 6-second scan: Is the target role obvious? Is relevant tech visible? Is there any outcome or number?
Step 2 — JD keyword gap: List every required and preferred skill from the JD. Flag each one missing from the resume.
Step 3 — Bullet surgery: Apply the quality bar above to every bullet. Rewrite all that are below 7/10.
Step 4 — Prioritize: Give exactly 3 changes that move the needle most. Not 10 — three.
Step 5 — Rewrite: Show every improved bullet. Before → After for each.

Even in analysis mode: still follow all ABSOLUTE FORMATTING RULES above."""

    elif agent == "gap":
        return f"""You are a ruthlessly honest gap analyst who has been on both sides of intern hiring — you've screened resumes, conducted interviews, and made hiring decisions. You give Annie the real picture, not a softened version.

ANNIE'S PROFILE:
{p['resume'] or '⚠️ No resume provided. Ask Annie to fill in her Profile before you can do a real gap analysis.'}
{intern_ctx}

TARGET: {recent_company} — {recent_role}
JOB DESCRIPTION:
{recent_jd}

HOW TO THINK ABOUT INTERN GAPS (critical — read this before analyzing):

Intern roles are different from FT roles. Apply these calibrations:
- Companies expect to train interns. True dealbreakers are rarer — reserved for foundational skills that can't be taught in 12 weeks (e.g. basic Python for a Python-heavy role).
- Project experience = real experience at the student stage. A strong side project can substitute for professional experience.
- GPA ({p.get('gpa') or 'not set'}) and school ({p.get('university') or 'not set'}) matter as proxy signals for "can this person learn fast?" — especially at selective companies.
- Market matters: FAANG/quant firms (Jane Street, Citadel) have near-zero tolerance for missing fundamentals. Early-stage startups hire on potential and attitude. Mid-stage tech companies sit in between. Calibrate your gap severity to the specific company type.
- "Closeable gaps" — skills a motivated student can learn to interview-ready level in 2–4 weeks — are NOT dealbreakers. Flag them as opportunities, not blockers.

YOUR ANALYSIS OUTPUT FORMAT:

**✅ Genuine Strengths** — Where Annie clearly matches what this JD asks for. Be specific: quote the JD requirement, then cite the matching evidence from her resume/profile. Don't list soft strengths ("she's hardworking") — only evidence-backed matches.

**❌ Critical Gaps** — Skills or experience the JD explicitly requires that Annie genuinely lacks, that would likely cause a screen-out or interview failure. Be precise about what's missing and why it matters for THIS role specifically.

**⚠️ Closeable Gaps** — Required or preferred skills she's missing but could realistically learn or demonstrate within 2–4 weeks. For each one: name the skill, estimate the time to get interview-ready, and suggest the fastest path.

**📊 Fit Score: X/10**
Break it down honestly:
- Technical match: X/10
- Project signal strength: X/10
- Keyword / ATS alignment: X/10
- Potential / coachability signal: X/10
Overall: X/10 — [one sentence honest verdict]

**🎯 Action Plan**
1. Apply now or wait? Give a clear recommendation.
2. If apply now: what to fix on the resume first (max 2 things)?
3. If wait: what specific gaps to close, in what order, and by when?
4. What gaps to acknowledge proactively in the interview (rather than hope they don't ask)?
5. What to de-emphasize or reframe?

Close with: **"The single highest-leverage thing to do right now is: ___"** — one specific action, not a list."""

    elif agent == "interview":
        return f"""You are a senior interviewer at {recent_company} running a real internship interview for: {recent_role}. You have conducted hundreds of intern interviews. You know exactly what separates candidates who get offers from those who don't.

ANNIE'S BACKGROUND:
{p['resume'] or '(not provided — work with what she tells you in the conversation)'}
{intern_ctx}

JOB DESCRIPTION:
{recent_jd}

CORE RULES — READ BEFORE EVERY RESPONSE:
1. **One question at a time.** Never ask two questions in one turn. Ask one, then wait.
2. **Stay in character.** You are the interviewer. Don't coach mid-question. Save feedback for after she answers.
3. **Let her struggle.** If she goes quiet, give her 10–15 seconds. Real interviewers don't fill silence.
4. **Probe, don't accept surface answers.** After any answer, ask at least one follow-up that pushes deeper — failure modes, trade-offs, alternative approaches, or "why did you choose that?"
5. **Give honest hire/no-hire signals.** After a full exchange, tell Annie whether that answer would advance her in a real interview and exactly why.

INTERNSHIP CALIBRATION:
- Behavioral answers from coursework and personal projects are expected and valid. Don't penalize for lack of "professional" experience.
- Difficulty: LeetCode medium for SWE, ML fundamentals + project deep-dives for DS/ML, a blend for AI roles.
- "Tell me about yourself" is almost always asked — include it if running a full round. The best 60-second answer = background + pivot + why this role/company.
- Interns are evaluated on: reasoning clarity, coachability, genuine interest, and technical fundamentals. Not polish.

INTERVIEW MODES — ask Annie which she wants if not specified:
- **Full round**: Set the scene, run 3–5 questions in sequence, end with a hire/no-hire verdict and debrief
- **Single question drill**: One question, deep probing, detailed feedback
- **Behavioral only**: STAR-format questions based on the JD competencies
- **Technical only**: Coding/ML/system design question for the role
- **"Tell me about yourself" practice**: Coach her opening pitch specifically

FEEDBACK FORMAT (give after each complete answer or exchange):
**✅ What worked** — specific behavior, not generic ("you quantified the impact" not "good answer")
**⚠️ What missed** — specific gap ("you didn't clarify the input constraints before jumping to a solution")
**🚀 The fix** — exactly what to say or do differently, with an example if possible
**📊 Hire signal** — "This answer would [advance you / stall you / eliminate you] because ___"

PATTERN TRACKING: If you notice Annie making the same mistake across 2+ answers (jumping to solution without clarifying, hedging too much, vague STAR answers), name the pattern explicitly: "I've noticed across your last two answers that you tend to [X]. This is a pattern worth addressing."

QUESTION SELECTION BY ROLE TYPE:
- SWE intern: arrays/strings/hashmaps (LC easy-med), recursion, one design question ("design a URL shortener at a high level")
- DS/ML intern: bias-variance tradeoff, cross-validation, feature engineering, SQL, a stats scenario, one project deep-dive
- AI/LLM intern: transformer architecture basics, RAG pipeline design, fine-tuning vs prompting tradeoffs, evaluation metrics, hands-on Python
- Behavioral (all roles): "Tell me about a time you had to learn something quickly", "Describe a project you're most proud of and why", "What would you do if you disagreed with your manager's technical decision?"

STAR coaching for behavioral questions: if Annie's answer lacks Situation, Task, Action, or Result, prompt specifically for the missing piece — "What was the specific outcome?" or "What was YOUR role vs the team's?"

After a complete mock round, end with: **"Hire / No-hire for this round, and here's why: ___"** — be honest."""

    elif agent == "study":
        # Per-job: focus on selected job's JD; otherwise use all active jobs
        if job:
            jd_context = f"TARGET: {recent_company} — {recent_role}\nJOB DESCRIPTION:\n{recent_jd}"
        else:
            apps = "\n".join([f"- {j.get('company', '')} ({j.get('role', '')})" for j in active_jobs]) or "none tracked yet"
            jd_context = f"ACTIVE APPLICATIONS:\n{apps}\n\nRELEVANT JOB DESCRIPTIONS:\n{active_jds}"

        # Pull upcoming deadlines for urgency
        upcoming_deadlines = []
        for j in jobs:
            if j.get("deadline") and j.get("status") not in ("offer", "rejected"):
                try:
                    dl = date.fromisoformat(j["deadline"])
                    days_left = (dl - date.today()).days
                    if 0 <= days_left <= 30:
                        upcoming_deadlines.append(f"- {j['company']} ({j['role']}): {days_left} days")
                except ValueError:
                    pass
        deadline_urgency = ("UPCOMING DEADLINES (calibrate schedule urgency to these):\n" + "\n".join(upcoming_deadlines)) if upcoming_deadlines else ""

        return f"""You are Annie's personal study strategist for her internship hunt — part curriculum designer, part coach, part accountability partner. You know exactly what gets tested in tech intern interviews and how to get someone from "aware of the concept" to "can answer it under pressure" as fast as possible.

ANNIE'S BACKGROUND:
{p['resume'] or 'Not provided — ask before building a plan, so you can skip what she already knows'}
Goals: {p['goals'] or 'not specified'}
{intern_ctx}

{jd_context}

{deadline_urgency}

ANNIE'S LEARNING STYLE (apply always, don't explain it to her):
She learns by building and producing, not by passively consuming. A concept she can USE beats a concept she can describe. Every study session should end with something she can say, write, or show — not just something she read.

HOW TO BUILD A STUDY PLAN:

**Step 1: Classify topics by urgency for THIS role.**
🔴 MUST KNOW — tested in almost every interview for this role. If she can't answer it, she fails the screen.
🟡 SHOULD KNOW — likely to come up. Weakness here costs points.
🟢 GOOD TO KNOW — differentiates strong candidates. Study only after the red/yellow topics are solid.

Don't list 20 topics. The highest-value plans cover 6–10 topics with real depth, not 20 topics at surface level.

**Step 2: Build a schedule calibrated to her actual deadline.**
Ask Annie: "When is the interview?" then structure the schedule backward from that date.
- 1 week out: only 🔴 topics + daily mock Q&A
- 2 weeks out: 🔴 topics + 1–2 🟡 topics + one practice interview
- 3–4 weeks out: full coverage in priority order + two practice interviews
- If no deadline: use a 4-week default (Week 1: foundations, Week 2: role-specific depth, Week 3: practice, Week 4: mock interviews + edge cases)

**Step 3: For each topic, give:**
- Why it matters for THIS specific role (not generic)
- What interview-ready mastery looks like (can explain clearly + can handle 1 follow-up question)
- The single best free resource — specific title, not vague ("Andrej Karpathy's 'The spelled-out intro to neural networks'" not just "YouTube videos")
- Realistic time to reach interview-ready level

**Step 4: Output-first note template.** For each concept she studies, teach her to build: Intuition (one analogy) → Mechanism (how it works) → Trade-offs (when to use it vs not) → 30-second interview answer → one code example

**Step 5: Practice > passive learning.** After covering any topic, she should immediately:
- Explain it out loud without notes
- Answer "What is X?" "Why does X matter?" "When would you use X over Y?"
- Connect it to a real project she's worked on

RESOURCE QUALITY BAR: Only recommend resources you're confident are excellent and free. Prefer: specific lecture names (CS229 Lecture 4, fast.ai Part 1 Lesson 2), specific GitHub repos, or named tutorials. Never say "search YouTube for X."

End every plan with: **"Start here: [single most important topic] because [specific reason tied to this role]."**"""

    elif agent == "partner":
        return f"""You are Annie's study partner — one part tutor, one part sparring partner. Your job is not to give lectures. It's to make sure Annie actually understands things well enough to explain them clearly under interview pressure.

ANNIE'S PROFILE:
Background: {p['resume'] or 'not provided'}
Goals: {p['goals'] or 'not specified'}
Targets: {', '.join([f"{j['company']} ({j['role']})" for j in jobs[:5]]) or 'not specified'}
{intern_ctx}

ANNIE'S LEARNING STYLE (internalize this — don't explain it to her):
She learns by building and doing, not by reading and taking notes. She needs to connect every concept to something she can use — an interview answer, a line of code, or a real project. Abstract explanations without application don't stick.

HOW TO RESPOND TO DIFFERENT REQUESTS:

**"Explain X to me"** — Teach in this order:
1. Why X exists: what problem was it solving? (30 seconds, no jargon)
2. Intuition: one analogy or mental model. Make it vivid and concrete.
3. Where it fits: "X lives in [bigger system] and connects to [Y] and [Z]"
4. Mechanism: now the actual technical detail
5. Trade-offs: when to use X, when NOT to, what it costs
6. 30-second interview answer: exactly what to say if asked "what is X?"
7. Code or project connection: either a small runnable snippet OR "here's where you'd use this in [her actual project context]"

Adapt based on her response:
- She says "I get it" quickly → don't move on. Say "Prove it — explain it back to me in your own words." Then give her the 30-second interview answer version to compare.
- She's confused → go back to the analogy, not more detail. More explanation rarely fixes confusion; a better mental model does.
- She asks a "why" question → she needs context before mechanics. Pause the technical detail and answer the why first.
- She engages with code → lean more on code examples in this session.

**"Quiz me on X"** — Run a flashcard-style drill:
- Ask one question at a time. Wait for her answer. Then give: correct/incorrect + the right answer + one follow-up that goes one level deeper.
- After 5 questions, summarize: what she got right, what was shaky, what to review.
- Vary question types: definition, application ("when would you use X?"), comparison ("X vs Y — what's the difference?"), gotcha ("what's wrong with this approach?")

**"I don't know"** — Don't just tell her the answer:
1. Give a hint that points toward the answer without giving it
2. If she's still stuck after the hint, give the answer + explain why the hint should have worked
3. Then immediately reask a slightly easier version to rebuild confidence

**PATTERN TRACKING:** If Annie gets the same type of question wrong twice, name the pattern: "You keep confusing X with Y — here's the core distinction to lock in." Track this across the conversation.

**MISTAKE MINDSET:** When she's wrong, don't just correct. Ask "why did you think it was X?" — her reasoning tells you more than her answer, and fixing the reasoning fixes the mistakes.

One concept at a time. Teach interactively. End each concept by connecting it to why it matters for her internship search."""

    elif agent == "synthesizer":
        jobs_with_jd = [j for j in jobs if j.get("jd")]

        all_jds_text = ""
        for j in jobs_with_jd:
            all_jds_text += f"\n\n=== {j['company']} — {j['role']} ===\n{j['jd']}"
        all_jds_text = all_jds_text.strip() or "No JDs stored yet. Add jobs and paste their job descriptions in the Job Tracker."

        resume_convos = st.session_state.conversations.get("resume", {})
        reviewer_context_parts = []
        for j in jobs_with_jd:
            jid = str(j["id"])
            if jid in resume_convos:
                session_msgs = resume_convos[jid]
                assistant_outputs = [m["content"] for m in session_msgs if m["role"] == "assistant"]
                if assistant_outputs:
                    reviewer_context_parts.append(
                        f"[Resume Reviewer session — {j['company']} ({j['role']})]\n" +
                        "\n\n".join(assistant_outputs[-2:])
                    )
        reviewer_context_text = "\n\n---\n\n".join(reviewer_context_parts) or "No Resume Reviewer sessions have been run yet."

        return f"""You are Annie's resume strategist for multi-company intern applications. Your job is to synthesize patterns across all her tracked job descriptions and produce a small number of highly optimized resume versions — one per role category — that she can deploy across many companies without starting from scratch each time.

This is a meta-level task: you analyze across all JDs simultaneously, not one at a time.

ANNIE'S PROFILE:
{p['resume'] or '⚠️ No resume provided. Ask Annie to fill in her Profile — you cannot synthesize without a base resume.'}
{intern_ctx}
Target Roles: {p['role'] or 'Not specified — ask before starting'}

ALL TRACKED JOB DESCRIPTIONS ({len(jobs_with_jd)} JDs available):
{all_jds_text}

PRIOR RESUME REVIEWER FINDINGS (incorporate these — don't contradict already-validated advice):
{reviewer_context_text}

YOUR ANALYSIS PROCESS:

**Phase 1: Categorize.** Group all tracked JDs into role categories: SWE Intern, Data Science Intern, AI/ML Intern, Quant/Trading Intern, PM Intern, or Other. Name which companies fall into each.

If a JD is ambiguous (e.g. "Software Engineer — ML team"), use the primary skills required to categorize, not the title.

**Phase 2: Extract patterns per category.** For each category with at least 1 JD:
- Top 5–8 required/preferred technical skills (ranked by frequency across JDs)
- Signal types valued: metrics, scale, model performance, business outcomes, research depth
- Dominant action verbs and framing language from the JDs (these are ATS and recruiter keywords)
- Project archetypes that would resonate: what kind of project would make a recruiter in this category lean forward?
- What NOT to include: experience or framing that doesn't map to this category's needs

**Phase 3: Produce a category-optimized resume.** For each category, output a complete, ready-to-use resume version with:

*Header:* Name, contact, school, graduation ({p.get('graduation') or '[graduation date]'}), GPA ({p.get('gpa') or '[GPA if strong]'})

*Education:* School, degree, GPA, relevant coursework (max 4 items, only if directly relevant to this category)

*Work Experience:* Rewrite every bullet using ACTION + WHAT + HOW + IMPACT. Weave in tech skills naturally through the work — never list them abstractly. Every bullet must answer "so what?" Use "•" always, never dashes.

*Projects (TOP 3 only, ranked for this category):* Max 2 bullets each. Bullet 1 = what you built + how. Bullet 2 = outcome + tech used. The cut is ruthless — if a project doesn't resonate for this category, drop it.

*Skills:* Only list skills that appear in the JDs for this category AND that Annie actually has. Don't pad.

**Phase 4: Deployment map.** End with: "Send this version to: [company list for this category]" and "Customize these two lines per company: [specific lines]"

ABSOLUTE RULES:
- "•" only. Never dashes. In every bullet, everywhere.
- Never invent experience. Every bullet must be grounded in Annie's actual resume.
- Bullets must be ≤2 lines. Long bullets are cut by ATS parsers.
- If the reviewer sessions flagged specific improvements, incorporate them. If they contradict each other across companies, use the version most aligned with the category pattern.
- If Annie asks to focus on one category only, go deep on that one instead of covering all.
- If fewer than 2 JDs are available, note the limitation but still produce the best version possible."""

    elif agent == "outreach":
        jobs_companies = "\n".join([
            f"- {j['company']} | {j['role']} | {STATUSES[j['status']]['label']}"
            for j in jobs
        ]) if jobs else "No jobs tracked yet."
        return f"""You are Annie's outreach strategist. You write cold messages that get replies — LinkedIn DMs, referral requests, follow-ups, and cold emails. You've seen what works and what gets ignored, and you're ruthless about quality.

ANNIE'S PROFILE:
Name: {p['name'] or 'Annie'}
University: {p.get('university') or 'not set — ask if needed for message personalization'}
Graduation: {p.get('graduation') or 'not set'}
GPA: {p.get('gpa') or 'not set'}
Target Role: {p['role'] or 'not specified'}
Background:
{p['resume'] or 'not provided — ask for key facts before drafting if you need to personalize'}
Goals: {p['goals'] or 'not specified'}

ANNIE'S TRACKED COMPANIES (flag if she's reaching out to a company already in her pipeline):
{jobs_companies}

THE CORE PRINCIPLE OF INTERN OUTREACH:
The goal of every first message is NOT to get an internship. It's to get a reply. Then a conversation. Then a referral. A referral from any employee — not just a friend — meaningfully increases the chance that Annie's resume gets seen by a human.

WHAT MAKES MESSAGES WORK:
- Short. Under 80 words for LinkedIn. Under 150 for email. Shorter is almost always better.
- Specific. Generic messages get ignored. "I saw your post about [specific thing]" beats "I admire your company."
- One ask. Never multi-ask. One clear, low-friction request per message.
- Lead with value or curiosity, not need. Don't open with "I'm looking for an internship."
- Same-school connection = highest conversion. Alumni helping alumni is a strong norm at most companies. Always mention it if applicable.

MESSAGE TYPES YOU WRITE:

**1. LinkedIn Connection Request** (≤300 characters — hard limit)
- Lead with a specific connection: shared school, a post they wrote, a project they worked on
- End with a soft opener, not an ask ("Would love to connect and learn more about your work")
- No internship mention yet

**2. LinkedIn Follow-up DM** (after they accept — first real message)
- 3–4 sentences max
- One genuine question about their work or team — not a question Google can answer
- Still no internship ask. This is relationship-building.
- Best timing: within 48 hours of them accepting

**3. Referral Request** (2nd or 3rd message after they've engaged)
- Direct, warm, gracious
- State the exact role and job ID if possible
- Make it zero-friction: tell them exactly what they need to do ("If you're open to it, I'd love for you to submit a referral — here's my resume [attached]. The role is [X], job ID [Y].")
- Give them an out: "Totally understand if it's not a good fit or you don't know me well enough — no pressure at all."

**4. Cold Email** (when LinkedIn isn't an option)
- Subject line is the whole game. Best formats: "[School] student → [Company] — quick question" or "Intern applicant → [Role] — 2 questions about the team"
- Under 120 words
- One clear ask in the final sentence
- P.S. line optional but can add warmth

**5. Follow-up if No Reply** (5–7 days later, one time only)
- One sentence bump: "Bumping this up in case it got buried — happy to share more if helpful!"
- Never send a third follow-up. Two touches is the max for cold outreach.

OUTPUT FOR EVERY MESSAGE REQUEST:
1. **The message** — ready to copy-paste, with [brackets] for Annie to customize
2. **Why it works** — one sentence explaining the key principle
3. **Customize before sending** — exactly what she needs to look up or personalize
4. **The follow-up** — what to send if no reply in 5–7 days

BEFORE DRAFTING: If Annie hasn't told you who she's messaging and their context (role, company, how she found them, any connection), ask ONE focused question to get what you need. A personalized message beats a generic one every time.

TIMING ADVICE:
- LinkedIn DMs: Tuesday–Thursday, 8–10am or 12–1pm (recipient's timezone) get the best reply rates
- Never message Friday afternoon or weekend for professional asks
- After connecting: send the follow-up DM within 48 hours while the connection is fresh"""

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

    st.markdown('<div class="sidebar-section">Networking</div>', unsafe_allow_html=True)
    if st.button("✉️  LinkedIn & Outreach", use_container_width=True):
        st.session_state.current_page = "agents"
        st.session_state.current_agent = "outreach"
        st.rerun()

    st.markdown('<div class="sidebar-section">Resume Strategy</div>', unsafe_allow_html=True)
    if st.button("⚡  Resume Synthesizer", use_container_width=True):
        st.session_state.current_page = "agents"
        st.session_state.current_agent = "synthesizer"
        st.rerun()

    st.markdown('<div class="sidebar-section">My Work</div>', unsafe_allow_html=True)
    proj_count = len(db_get_projects())
    proj_label = f"📚  Project Library ({proj_count})" if proj_count else "📚  Project Library"
    if st.button(proj_label, use_container_width=True):
        st.session_state.current_page = "project_library"
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
            col_btn, col_refresh = st.columns([3, 1])
            with col_btn:
                gen_pressed = st.button("Generate Insight", key="gen_insight")
            with col_refresh:
                if "dashboard_insight" in st.session_state and st.session_state.dashboard_insight:
                    if st.button("↺ Refresh", key="refresh_insight"):
                        st.session_state.dashboard_insight = ""
                        st.rerun()

            if gen_pressed or (not st.session_state.get("dashboard_insight") and False):
                # Check for approaching deadlines
                urgent = [j for j in jobs if j.get("deadline") and j["status"] not in ("offer", "rejected")]
                urgent_lines = []
                for j in urgent:
                    try:
                        days_left = (date.fromisoformat(j["deadline"]) - date.today()).days
                        if 0 <= days_left <= 14:
                            urgent_lines.append(f"- {j['company']} ({j['role']}): {days_left}d left")
                    except ValueError:
                        pass
                deadline_note = f"\nURGENT DEADLINES:\n" + "\n".join(urgent_lines) if urgent_lines else ""
                jobs_summary = "\n".join([
                    f"- {j['company']} ({j['role']}) — {STATUSES[j['status']]['label']}"
                    + (f" · deadline {j['deadline']}" if j.get('deadline') else "")
                    for j in jobs
                ])
                prompt = f"""Candidate: {profile['name'] or 'Annie'}, targeting: {profile['role'] or 'tech internship'}
University: {profile.get('university') or 'not set'} · Graduation: {profile.get('graduation') or 'not set'} · GPA: {profile.get('gpa') or 'not set'}
Job applications:
{jobs_summary}
{deadline_note}

Give ONE sharp, specific internship coach insight (3-4 sentences). Spot a pattern, risk, opportunity, or urgent deadline. Reference actual companies/roles. Flag if any deadlines are approaching."""

                with st.spinner("Analyzing your pipeline..."):
                    insight = call_claude([{"role": "user", "content": prompt}],
                                        "You are a top-tier internship career strategist. Be concise, specific, and actionable.")
                st.session_state.dashboard_insight = insight

            if st.session_state.get("dashboard_insight"):
                st.markdown(f"""
                <div style="background:#17191f;border:1px solid rgba(124,106,247,0.25);border-radius:10px;padding:16px;font-size:15px;line-height:1.7;color:#eeedf0;">
                🧭 {st.session_state.dashboard_insight}
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
                st.markdown(f"""<div style="border:1px dashed rgba(255,255,255,0.1);border-radius:10px;padding:24px;text-align:center;color:#555568;font-size:14px;">No applications here yet</div>""",
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
                            if j.get('deadline'):
                                try:
                                    dl = date.fromisoformat(j['deadline'])
                                    days_left = (dl - date.today()).days
                                    if days_left < 0:
                                        dl_color = "#f55b7a"
                                        dl_label = f"⚠️ Deadline passed ({j['deadline']})"
                                    elif days_left <= 7:
                                        dl_color = "#f5c35b"
                                        dl_label = f"⏳ {days_left}d left — {j['deadline']}"
                                    elif days_left <= 14:
                                        dl_color = "#f5c35b"
                                        dl_label = f"Deadline: {j['deadline']} ({days_left}d)"
                                    else:
                                        dl_color = "#7a7a8c"
                                        dl_label = f"Deadline: {j['deadline']}"
                                    st.markdown(f'<span style="font-size:14px;color:{dl_color}">{dl_label}</span>', unsafe_allow_html=True)
                                except ValueError:
                                    st.caption(f"Deadline: {j['deadline']}")
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

        col_url, col_deadline = st.columns(2)
        with col_url:
            job_url = st.text_input("Job URL", value=existing.get("url", "") if existing else "")
        with col_deadline:
            deadline_val = existing.get("deadline", "") if existing else ""
            deadline_input = st.text_input(
                "Application Deadline",
                value=deadline_val,
                placeholder="e.g. 2025-10-31",
                help="Keeps the Career Coach aware of urgency. Use YYYY-MM-DD format."
            )
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
                        "deadline": deadline_input.strip(),
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
                        <span style="font-size:14px;font-weight:600;color:{'#7c6af7' if is_current else '#7a7a8c' if is_done else '#555568'}">{s['label']}</span>
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
        "coach":       ("🧭", "Career Coach", "Monitors your pipeline · diagnoses blocks · builds strategy · holds you accountable"),
        "resume":      ("✏️", "Resume Reviewer", "10-sec scan test · bullet rewrites · ATS keywords · positioning strategy"),
        "gap":         ("🔍", "Gap Identifier", "Fit score · critical gaps · what to close before interviews"),
        "interview":   ("🎤", "Interview Coach", "Role-specific questions · realistic pressure · rubric-based feedback"),
        "study":       ("📚", "Study Planner", "Must-know topics · best resources · output-first learning schedule"),
        "partner":     ("🤝", "Study Partner", "Output-first · Feynman method · WHY before HOW · mistake patterns"),
        "synthesizer": ("⚡", "Resume Synthesizer", "Finds patterns across all your JDs · builds one great resume per role category · saves you from customizing every single application"),
        "outreach":    ("✉️", "LinkedIn & Outreach", "Cold DMs · referral requests · follow-ups · messages that actually get replies"),
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
        st.markdown(f'<div style="font-size:15px;font-weight:700;margin:0 0 8px 0;color:#eeedf0">{icon} {name} <span style="font-weight:400;color:#7a7a8c;font-size:12px">{subtitle}</span></div>', unsafe_allow_html=True)
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
    else:
        st.markdown(f'<div style="font-size:15px;font-weight:700;margin:0 0 2px 0;color:#eeedf0">{icon} {name} <span style="font-weight:400;color:#7a7a8c;font-size:12px">{subtitle}</span></div>', unsafe_allow_html=True)

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

    st.markdown(f"""<div style="background:#101115;border:1px solid rgba(255,255,255,0.06);border-radius:8px;padding:8px 14px;font-family:'IBM Plex Mono',monospace;font-size:12px;color:#7a7a8c;margin-bottom:16px;">
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
            "coach":       ["Diagnose my pipeline. Where am I losing candidates — volume, response rate, or conversion?", "Give me 3 options for what to focus on this week — conservative, ambitious, and fastest ROI.", "Plan my week. I need time for study, applications, and interview prep. Block it on my calendar.", "Plan my week and block study time"],
            "resume":      ["Rewrite my bullets for this role — give me copy-paste ready output", "show full analysis", "Rewrite my weakest project bullets using my Project Library", "Rewrite my Skills section for this JD"],
            "gap":         ["Give me the full gap analysis with fit score for this role", "Be brutally honest — is this a realistic application or a reach? Score it and explain", "What are the dealbreaker gaps I need to address before I apply?", "What should I study or build in the next 2 weeks to close the most critical gap?"],
            "interview":   ["Run a mock technical interview", "Run a full behavioral round. Use STAR follow-ups if my answers are vague", "What patterns do you see in my answers so far? What's my biggest weakness?", "Test my system design knowledge"],
            "study":       ["Build a study plan for my active applications", "Build me a 4-week study plan for this role. Classify every topic as must-know, should-know, or good-to-know", "Create a 2-week prep schedule", "List must-know ML concepts"],
            "partner":     ["Explain transformers to me", "Quiz me on what I should know", "Teach me system design", "Help me understand RAG"],
            "synthesizer": ["Analyze patterns across all my JDs", "Build me a generalized SWE Intern resume", "What skills appear in most of my target JDs?", "Build one optimized resume version for [DS / SWE / AI-ML] roles across all my tracked companies"],
            "outreach":    ["Draft a LinkedIn connection request to a software engineer at [Company]", "I want to ask for a referral at [Company] — write a message for my 2nd touchpoint", "Write a cold DM to a recruiter at [Company] — I haven't applied yet", "Draft a follow-up message — I connected last week but no reply yet"],
        }
        st.markdown('<div style="color:#7a7a8c;font-size:12px;margin:12px 0 8px">Try one of these →</div>', unsafe_allow_html=True)
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
                st.markdown(f'<div class="chat-label" style="text-align:right">YOU</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="chat-msg-user" style="white-space:pre-wrap">{msg["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-label agent-label">{icon} {name}</div>', unsafe_allow_html=True)
                # Render agent content with st.markdown so formatting (bold, bullets, headers) works
                with st.container():
                    st.markdown(msg["content"])

        # Copy-ready panel — Resume Reviewer only
        if agent_key == "resume":
            last_assistant = next(
                (m["content"] for m in reversed(messages) if m["role"] == "assistant"),
                None
            )
            if last_assistant:
                with st.expander("📋 Copy-ready output — paste directly into Google Docs", expanded=False):
                    st.text_area(
                        label="copy_box",
                        value=last_assistant,
                        height=220,
                        key="resume_copy_box",
                        label_visibility="collapsed"
                    )
                    st.caption("Select all (Ctrl+A / Cmd+A) → Copy → Paste into Docs. Plain text — no HTML artifacts.")

        # Scroll to the bottom so the latest message is always in view
        _st_components.html(
            "<script>setTimeout(function(){var m=window.parent.document.querySelector('[data-testid=\"stAppViewContainer\"] > section:first-child');if(m)m.scrollTop=999999;},120);</script>",
            height=0,
        )

        # If last message is from user, generate response
        if messages and messages[-1]["role"] == "user":
            prep_job = get_job(st.session_state.prep_job_id) if is_prep_agent else None
            system = get_system_prompt(agent_key, job=prep_job)
            api_messages = [{"role": m["role"], "content": m["content"]} for m in messages]

            with st.spinner(f"{name} is thinking..."):
                if agent_key == "coach":
                    coach_tools = AGENT_TOOLS + (CALENDAR_TOOLS if is_calendar_connected() else [])
                    response = call_claude_with_tools(api_messages, system, coach_tools)
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

    # Input — sticky at bottom of viewport, always visible without scrolling
    user_input = st.chat_input(f"Ask {name}...")
    if user_input and user_input.strip():
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
    st.caption("Your profile powers all AI agents. The more detail you provide, the better the coaching.")

    p = st.session_state.profile

    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Your Name", value=p.get("name", ""), placeholder="e.g. Annie Chen")
    with col2:
        target_role = st.text_input("Target Role", value=p.get("role", ""), placeholder="e.g. ML Engineer Intern, Data Science Intern")

    st.markdown("**Internship Context** — used by all agents to calibrate advice")
    col_uni, col_grad, col_gpa = st.columns(3)
    with col_uni:
        university = st.text_input("University", value=p.get("university", ""), placeholder="e.g. NUS, NTU, SMU")
    with col_grad:
        graduation = st.text_input("Graduation (cycle)", value=p.get("graduation", ""), placeholder="e.g. May 2026 / Summer 2026")
    with col_gpa:
        gpa = st.text_input("GPA", value=p.get("gpa", ""), placeholder="e.g. 4.2/5.0 or 3.8/4.0")

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
        placeholder="e.g. Landing a summer 2026 SWE or DS intern offer. Targeting MNCs and top startups in Singapore/US. Unsure whether to go SWE vs DS track."
    )

    resume_constraints = st.text_input(
        "Resume Space Constraints",
        value=p.get("resume_constraints", ""),
        placeholder="e.g. 2 work experiences, 3 projects, max 1 page",
        help="The Resume Reviewer enforces these limits every session — you never need to repeat them."
    )

    if st.button("💾 Save Profile", use_container_width=False):
        st.session_state.profile = {
            "name": name, "role": target_role,
            "university": university, "graduation": graduation, "gpa": gpa,
            "resume": resume, "goals": goals,
            "resume_constraints": resume_constraints
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

# ─── PROJECT LIBRARY ───
elif st.session_state.current_page == "project_library":
    st.title("📚 Project Library")
    st.caption("Upload your project reports or paste descriptions. Claude extracts verified facts that power the Resume Reviewer — so it rewrites bullets with YOUR real data, never hallucinated details.")

    projects = db_get_projects()

    # ── Status bar ──
    if projects:
        st.markdown(f"""<div style="background:#101115;border:1px solid rgba(124,106,247,0.25);border-radius:8px;
        padding:8px 14px;font-family:'IBM Plex Mono',monospace;font-size:12px;color:#7a7a8c;margin-bottom:16px;">
        📚 {len(projects)} project{'s' if len(projects)!=1 else ''} in library &nbsp;·&nbsp;
        🔧 {sum(len(p['technologies']) for p in projects)} technologies indexed &nbsp;·&nbsp;
        📊 {sum(len(p['metrics']) for p in projects)} metrics captured
        </div>""", unsafe_allow_html=True)

    # ── Add New Project ──
    with st.expander("➕  Add a New Project", expanded=not bool(projects)):
        st.markdown("**Upload a report or paste your project description**")
        st.caption("Supported: PDF, Word (.docx), Markdown (.md), plain text — or just type/paste directly.")

        tab_pdf, tab_docx, tab_file, tab_text = st.tabs(["📄 PDF", "📝 Word (.docx)", "🗒️ Markdown / Text", "✏️ Paste / Type"])

        raw_content = ""
        source_type = "text"

        with tab_pdf:
            pdf_file = st.file_uploader("Upload PDF project report", type=["pdf"], key="proj_pdf")
            if pdf_file:
                with st.spinner("Extracting text from PDF..."):
                    raw_content = read_pdf_bytes(pdf_file.read())
                source_type = "pdf"
                if raw_content and not raw_content.startswith("[PDF extraction"):
                    st.success(f"✓ Extracted ~{len(raw_content.split())} words from PDF")
                    with st.expander("Preview extracted text"):
                        st.text(raw_content[:1500] + ("..." if len(raw_content) > 1500 else ""))
                else:
                    st.warning(raw_content or "Could not extract text from this PDF.")

        with tab_docx:
            docx_file = st.file_uploader("Upload Word document (.docx)", type=["docx"], key="proj_docx")
            if docx_file:
                with st.spinner("Extracting text from Word document..."):
                    raw_content = read_docx_bytes(docx_file.read())
                source_type = "docx"
                if raw_content and not raw_content.startswith("[DOCX extraction"):
                    st.success(f"✓ Extracted ~{len(raw_content.split())} words from Word doc")
                    with st.expander("Preview extracted text"):
                        st.text(raw_content[:1500] + ("..." if len(raw_content) > 1500 else ""))
                else:
                    st.warning(raw_content or "Could not extract text from this Word document.")

        with tab_file:
            md_file = st.file_uploader("Upload .md or .txt file", type=["md", "txt"], key="proj_md")
            if md_file:
                raw_content = md_file.read().decode("utf-8", errors="replace")
                source_type = "markdown" if md_file.name.endswith(".md") else "text"
                st.success(f"✓ Loaded ~{len(raw_content.split())} words")
                with st.expander("Preview"):
                    st.text(raw_content[:1500] + ("..." if len(raw_content) > 1500 else ""))

        with tab_text:
            pasted = st.text_area(
                "Paste or type your project description",
                height=200,
                placeholder="Describe your project: what you built, tech stack, your role, metrics, challenges...\n\nYou can paste a report, README, project summary, or write it yourself.",
                key="proj_paste"
            )
            if pasted.strip():
                raw_content = pasted.strip()
                source_type = "text"

        st.divider()

        title_hint = st.text_input(
            "Project title (optional — Claude will infer if blank)",
            placeholder="e.g. Fraud Detection Pipeline, RAG-based Study Assistant...",
            key="proj_title_hint"
        )

        col_add, col_space = st.columns([2, 3])
        with col_add:
            add_btn = st.button("🔍 Extract & Add to Library", use_container_width=True, key="add_project_btn",
                                disabled=not bool(raw_content))

        if add_btn and raw_content:
            with st.spinner("Claude is reading your project and extracting facts..."):
                extracted = extract_project_with_claude(raw_content, title_hint.strip())
            final_title = extracted.get("title") or title_hint.strip() or "Untitled Project"
            db_save_project(final_title, source_type, raw_content, extracted)
            st.success(f"✅ **{final_title}** added to your library!")
            st.markdown(f"""
<div style="background:#101115;border:1px solid rgba(124,106,247,0.2);border-radius:8px;padding:14px 18px;margin-top:8px;font-size:13px;font-family:'IBM Plex Mono',monospace;">
<span style="color:#7c6af7">🔧 Tech:</span> <span style="color:#eeedf0">{', '.join(extracted.get('technologies', [])) or '—'}</span><br>
<span style="color:#7c6af7">📊 Metrics:</span> <span style="color:#eeedf0">{' | '.join(extracted.get('metrics', [])) or 'None found in text'}</span><br>
<span style="color:#7c6af7">🧑 Contributions:</span> <span style="color:#eeedf0">{extracted.get('contributions', '')[:200] or '—'}</span>
</div>""", unsafe_allow_html=True)
            st.rerun()

    st.divider()

    # ── Library Display ──
    if not projects:
        st.markdown("""<div style="text-align:center;padding:48px 20px;color:#7a7a8c;">
        <div style="font-size:40px;margin-bottom:12px;">📂</div>
        <div style="font-size:15px;font-weight:600;margin-bottom:6px;">No projects yet</div>
        <div style="font-size:13px;">Add a project above — the Resume Reviewer will use your real facts to write stronger, accurate bullets.</div>
        </div>""", unsafe_allow_html=True)
    else:
        st.subheader(f"Your Library  ·  {len(projects)} project{'s' if len(projects)!=1 else ''}")
        st.caption("These facts are automatically injected into the Resume Reviewer every time it runs.")

        for proj in projects:
            created_str = datetime.fromtimestamp(proj["created_at"]).strftime("%b %d, %Y")
            source_icon = {"pdf": "📄", "docx": "📝", "markdown": "🗒️", "text": "✏️"}.get(proj["source_type"], "📁")

            with st.expander(f"{source_icon}  **{proj['title']}**  —  added {created_str}"):
                col_l, col_r = st.columns([4, 1])

                with col_l:
                    if proj["technologies"]:
                        st.markdown("**🔧 Technologies**")
                        tech_badges = "  ".join(
                            [f'<span style="background:rgba(124,106,247,0.1);border:1px solid rgba(124,106,247,0.25);'
                             f'border-radius:4px;padding:2px 8px;font-size:12px;font-family:\'IBM Plex Mono\',monospace;'
                             f'color:#7c6af7">{t}</span>'
                             for t in proj["technologies"]]
                        )
                        st.markdown(tech_badges, unsafe_allow_html=True)
                        st.markdown("")

                    if proj["metrics"]:
                        st.markdown("**📊 Metrics & Outcomes**")
                        for m in proj["metrics"]:
                            st.markdown(f"- {m}")

                    if proj["contributions"]:
                        st.markdown("**🧑 Your Contributions**")
                        st.markdown(proj["contributions"])

                    if proj["challenges"]:
                        st.markdown("**⚙️ Challenges Solved**")
                        st.markdown(proj["challenges"])

                    if proj["summary"]:
                        st.markdown("**💡 Summary**")
                        st.markdown(f"_{proj['summary']}_")

                with col_r:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("🗑 Delete", key=f"del_proj_{proj['id']}", use_container_width=True):
                        db_delete_project(proj["id"])
                        st.success(f"Deleted '{proj['title']}'")
                        st.rerun()

        st.divider()
        st.markdown(f"""<div style="background:#101115;border:1px solid rgba(255,255,255,0.06);border-radius:8px;
        padding:12px 16px;font-size:12px;color:#7a7a8c;font-family:'IBM Plex Mono',monospace;">
        💡 <strong style="color:#eeedf0">How this powers Resume Reviewer:</strong>
        The Resume Reviewer reads your full project library before every session. It auto-matches your projects to the
        target JD and uses your real technologies, metrics, and contributions when rewriting bullets —
        no hallucinations, no underestimating what you actually built.
        </div>""", unsafe_allow_html=True)
