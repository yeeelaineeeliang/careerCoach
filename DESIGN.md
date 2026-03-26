# CareerOS — Design & Architecture Documentation

> **Purpose of this document:** Complete reference for the current system design, code structure, agent behavior, data model, and planned future architecture. Use this as the starting context for any new implementation session.
>
> **Last updated:** March 2026 — reflects full implementation including Project Library, per-job agents, Resume Synthesizer, Google Calendar, and Doraemon companion widget.

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [File Structure](#2-file-structure)
3. [Tech Stack](#3-tech-stack)
4. [Data Model](#4-data-model)
5. [Persistence Layer (SQLite)](#5-persistence-layer-sqlite)
6. [Session State](#6-session-state)
7. [UI Architecture](#7-ui-architecture)
8. [Agent System](#8-agent-system)
9. [Agent System Prompts — Design Decisions](#9-agent-system-prompts--design-decisions)
10. [Project Library — Architecture & Agent Integration](#10-project-library--architecture--agent-integration)
11. [Google Calendar Integration](#11-google-calendar-integration)
12. [Routing & Navigation](#12-routing--navigation)
13. [Job Tracker — CRUD & Status Flow](#13-job-tracker--crud--status-flow)
14. [API Key Handling](#14-api-key-handling)
15. [Companion Widget (Doraemon)](#15-companion-widget-doraemon)
16. [Known Limitations of Current System](#16-known-limitations-of-current-system)
17. [Future Architecture — Multi-Agent System](#17-future-architecture--multi-agent-system)
18. [Design Decisions Log](#18-design-decisions-log)

---

## 1. System Overview

CareerOS is a single-file Streamlit application that combines:

- A **Kanban job tracker** (6 status columns, per-job progress timeline, JD storage)
- A **dashboard** with live pipeline stats and on-demand Career Coach insight
- **7 specialized AI agents** each powered by Claude with deeply personalized system prompts
- A **Project Library** — a persistent knowledge base of the user's past work, used to ground resume rewrites in real facts
- **SQLite persistence** so all data survives restarts
- **Google Calendar integration** so the Career Coach can read and create events
- A **floating Doraemon companion** widget for ambient encouragement

The system is designed around one core idea: **agents should be useful because they have context, not because the user re-explains themselves every session.** Profile, job tracker data, JDs, and project history are all injected into relevant agent system prompts at call time.

### Current state vs. future goal

| Dimension | Current (v1) | Target (v2 Multi-Agent) |
|---|---|---|
| Architecture | 7 isolated chatbots | Coordinated LangGraph agent graph |
| Shared memory | None between agents | `CareerOSState` TypedDict, shared findings |
| Project knowledge | Project Library → Resume agent | All agents can query Project Library |
| Orchestration | User manually navigates | Career Coach routes to sub-agents automatically |
| Tool use | Calendar (Coach only) | Web search, file generation, calendar for all agents |
| Persistence | Manual `db_save` calls | LangGraph checkpointer on same SQLite file |

---

## 2. File Structure

```
careerCoach/
├── app.py                  # Entire application — single file (~2,200 lines)
├── requirements.txt        # Python dependencies (see Section 3)
├── careeros.db             # SQLite database — auto-created on first run (gitignore)
├── google_credentials.json # OAuth credentials for Google Calendar (gitignore)
├── DESIGN.md               # This document
├── README.md               # User-facing setup and usage guide
└── USER_GUIDE.md           # Detailed feature walkthrough
```

**Why single file:** Streamlit's execution model re-runs the entire script on every interaction. Splitting into modules is possible but adds import complexity with no current benefit given the app's size. Threshold for splitting: when any logical group exceeds ~500 lines or when the agent system moves to LangGraph nodes.

---

## 3. Tech Stack

| Layer | Technology | Notes |
|---|---|---|
| UI framework | Streamlit 1.35+ | `st.session_state` for in-memory state, `st.rerun()` for re-renders |
| LLM — agents | Anthropic `claude-opus-4-5` | All 7 chat agents use this model |
| LLM — extraction | Anthropic `claude-haiku-4-5-20251001` | Project Library extraction only — fast + cheap |
| Persistence | SQLite3 (stdlib) | Two tables: `kv` (key-value) and `projects` |
| PDF parsing | `pypdf >= 4.0.0` | Extracts text page-by-page from uploaded reports |
| DOCX parsing | `python-docx >= 1.1.0` (primary) + stdlib zipfile/XML (fallback) | Extracts paragraphs and table rows from Word documents |
| Calendar | Google Calendar API v3 via `google-api-python-client` | OAuth2, credentials stored in `google_credentials.json` |
| Styling | Custom CSS via `st.markdown` | Dark theme, Syne + IBM Plex Mono fonts from Google CDN |
| JS injection | `streamlit.components.v1.html(height=0)` | Used for Doraemon widget — scripts can't run via `st.markdown` |
| Python | 3.10+ | Uses `pathlib`, `datetime`, `typing`, `zipfile`, `xml.etree` |

### Dependencies (`requirements.txt`)
```
streamlit>=1.35.0
anthropic>=0.28.0
python-dotenv>=1.0.0
google-api-python-client>=2.100.0
google-auth-httplib2>=0.1.0
google-auth-oauthlib>=1.1.0
pypdf>=4.0.0
python-docx>=1.1.0
```

---

## 4. Data Model

### 4.1 Profile
```python
{
    "name":   str,   # e.g. "Annie Chen"
    "role":   str,   # e.g. "ML Engineer"
    "resume": str,   # Full resume text, plain text
    "goals":  str    # Free-form current situation + objectives
}
```
**DB key:** `"profile"` (in `kv` table)

### 4.2 Job
```python
{
    "id":         int,            # Auto-incrementing, never reused
    "company":    str,            # Required
    "role":       str,
    "status":     str,            # wishlist | applied | screen | interview | offer | rejected
    "date":       str,            # ISO "YYYY-MM-DD"
    "location":   str,
    "salary":     str,            # Free text, e.g. "$120k–$160k"
    "url":        str,
    "tags":       list[str],      # e.g. ["ML", "startup", "Python"]
    "jd":         str,            # Full job description — critical for per-job agents
    "notes":      str,            # Personal notes (not surfaced to agents)
    "progress":   list[ProgressNote],
    "created_at": float           # Unix timestamp, used for sorting
}
```

### 4.3 ProgressNote
```python
{
    "status": str,   # Stage this note is attached to
    "note":   str,
    "date":   str    # ISO "YYYY-MM-DD"
}
```

### 4.4 Conversations
Per-job agents store histories keyed by `job_id`. Global agents store flat lists.
```python
{
    # Global agents — flat message lists
    "coach":       list[Message],
    "partner":     list[Message],
    "synthesizer": list[Message],

    # Per-job agents — dict keyed by str(job_id)
    "resume":    { "42": list[Message], "43": list[Message], ... },
    "gap":       { "42": list[Message], ... },
    "interview": { "42": list[Message], ... },
    "study":     { "42": list[Message], ... },
}
```
**DB key:** `"conversations"` (in `kv` table)

### 4.5 Message
```python
{
    "role":    "user" | "assistant",
    "content": str
}
```
Matches the Anthropic API messages format exactly — no transformation needed before API calls.

### 4.6 Project (SQLite `projects` table)
```python
{
    "id":            int,       # AUTOINCREMENT primary key
    "title":         str,       # Extracted or user-provided title
    "source_type":   str,       # "pdf" | "docx" | "markdown" | "text"
    "raw_content":   str,       # Original extracted text (capped at 60,000 chars)
    "technologies":  list[str], # e.g. ["Python", "FastAPI", "PostgreSQL"]
    "metrics":       list[str], # Exact numeric facts from the text only
    "contributions": str,       # First-person description of what the user built/owned
    "challenges":    str,       # Key technical problems solved
    "summary":       str,       # 2-sentence summary for JD matching
    "created_at":    float      # Unix timestamp
}
```
Technologies and metrics stored as JSON strings in SQLite. Deserialized on read.

### 4.7 Status Enum
```python
STATUSES = {
    "wishlist":  {"label": "Wishlist",     "color": "#7a7a8c", "icon": "◇"},
    "applied":   {"label": "Applied",      "color": "#5bc8f5", "icon": "→"},
    "screen":    {"label": "Phone Screen", "color": "#f5c35b", "icon": "☎"},
    "interview": {"label": "Interview",    "color": "#a55bf5", "icon": "✦"},
    "offer":     {"label": "Offer",        "color": "#c5f135", "icon": "★"},
    "rejected":  {"label": "Rejected",     "color": "#f55b7a", "icon": "✕"},
}
```

---

## 5. Persistence Layer (SQLite)

### Schema

**Table 1: `kv`** — key-value store for profile, jobs, conversations
```sql
CREATE TABLE IF NOT EXISTS kv (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
```
Steady-state rows: `profile`, `jobs`, `next_job_id`, `conversations`.

**Table 2: `projects`** — structured project knowledge base
```sql
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
);
```

Both tables live in the same `careeros.db` file. `_db()` creates `kv`; `_projects_db()` creates `projects`.

### KV Functions
```python
def _db() -> sqlite3.Connection          # Opens connection, ensures kv table exists
def db_save(key, value) -> None          # INSERT OR REPLACE, json.dumps with default=str
def db_load(key, default=None) -> any    # Returns parsed JSON or default
def db_load_all() -> dict                # One query at startup — all rows
```

### Projects Functions
```python
def _projects_db() -> sqlite3.Connection             # Opens connection, ensures projects table
def db_save_project(title, source_type,
                    raw_content, extracted) -> int    # INSERT, returns new project id
def db_get_projects() -> list[dict]                  # All projects, newest first
def db_delete_project(project_id: int) -> None       # DELETE by id
```

### Save Points

| Action | Save call |
|---|---|
| Add / update / delete job | `db_save("jobs", ...)` |
| Profile save | `db_save("profile", ...)` |
| Any agent message (send or receive) | `db_save("conversations", ...)` |
| Clear chat | `db_save("conversations", ...)` |
| Add project | `db_save_project(...)` |
| Delete project | `db_delete_project(id)` |

### Startup Load
```python
if "_db_loaded" not in st.session_state:
    saved = db_load_all()
    st.session_state.profile       = saved.get("profile", {...defaults})
    st.session_state.jobs          = saved.get("jobs", [])
    st.session_state.next_job_id   = saved.get("next_job_id", 1)
    st.session_state.conversations = _migrate_conversations(saved.get("conversations", {}), ...)
    st.session_state._db_loaded    = True
```
`_db_loaded` flag prevents re-loading on every Streamlit re-run. Projects are loaded directly from DB on demand (not cached in session state) to avoid stale data.

---

## 6. Session State

### Persisted (survives restart via SQLite)
| Key | Type | Description |
|---|---|---|
| `profile` | dict | Name, role, resume, goals |
| `jobs` | list[dict] | All job applications |
| `next_job_id` | int | Auto-increment counter |
| `conversations` | dict | Per-agent and per-job chat histories |

### UI-only (reset on restart, intentional)
| Key | Type | Description |
|---|---|---|
| `api_key` | str | Loaded from env, never persisted (security) |
| `current_page` | str | `dashboard` / `tracker` / `add_job` / `agents` / `profile` / `project_library` |
| `current_agent` | str | `coach` / `resume` / `gap` / `interview` / `study` / `partner` / `synthesizer` |
| `selected_job_id` | int\|None | Currently viewed job in tracker |
| `prep_job_id` | int\|None | Job selected for per-job agents (Resume, Gap, Interview, Study) |
| `_db_loaded` | bool | Guard flag — prevents DB reload on every re-run |

### Conversation Migration
`_migrate_conversations(raw, jobs)` handles upgrading old flat conversation format to the per-job dict format. Old flat `"resume"` list is moved to the first job that has a JD. Coach, Partner, Synthesizer remain flat lists.

---

## 7. UI Architecture

### Layout
```
Streamlit wide layout
├── Global CSS injection (st.markdown, ~200 lines)
├── Doraemon widget (st.markdown HTML + components.v1.html JS, height=0)
├── Sidebar (always visible)
│   ├── Logo: "CareerOS" + "Job Hunt Command Center"
│   ├── Overview: Dashboard, Job Tracker
│   ├── Career Coach: Career Coach
│   ├── Job Preparation: Resume Reviewer, Gap Identifier, Interview Coach, Study Planner
│   ├── Study: Study Partner
│   ├── Resume Strategy: Resume Synthesizer
│   ├── My Work: Project Library (with live count badge)
│   ├── Settings: My Profile
│   └── Mini stats bar (applied · active · interviews · offers · rate)
└── Main content (page-routed)
    ├── Dashboard
    ├── Job Tracker (Kanban, tabbed by status)
    ├── Add/Edit Job (3-tab form)
    ├── Agents (chat interface with job selector for per-job agents)
    ├── Profile
    └── Project Library
```

### Styling

All styling is injected as a single `<style>` block via `st.markdown(..., unsafe_allow_html=True)` at the top of the file. The block is never split — keeping it together makes it easier to reason about specificity.

**Color palette:**
```
Background:    #080910   near-black
Surface 1:     #0f1015   sidebar, status bars
Surface 2:     #161720   cards, inputs, agent messages
Surface 3:     #1e2030   user messages
Accent lime:   #c5f135   primary CTA, active states, headings, badges
Accent sky:    #5bc8f5   applied status
Accent amber:  #f5c35b   screen status
Accent violet: #a55bf5   interview status
Accent rose:   #f55b7a   rejected status
Text primary:  #eeedf0
Text muted:    #7a7a8c
```

**Fonts:** Syne (headings, buttons, labels) + IBM Plex Mono (monospace: stats, badges, status text). Loaded from Google CDN via `@import`.

**Key CSS rules:**
- `body, .main, p, span, label, div { color: #eeedf0 !important }` — global dark theme
- `.stButton > button p/span/div { color: #080910 !important }` — fixes button text (Streamlit renders labels in `<p>` which inherits the global override)
- `.stTextArea > div > div > textarea { resize: vertical !important; min-height: 60px !important }` — all textareas are vertically resizable
- Custom classes: `.chat-msg-user`, `.chat-msg-agent`, `.badge-*`, `.job-card`, `.sidebar-section`

### Chat Input
The agent chat input uses `st.text_area` (not `st.text_input`) for multi-line support. Height starts at 80px, draggable to any height. The Send button is offset by a `<div style="height:28px">` spacer to align with the textarea. Submission requires clicking Send (Enter adds newline, Shift+Enter is not needed).

### JavaScript Injection Pattern
Streamlit's `st.markdown(unsafe_allow_html=True)` renders HTML through React's `dangerouslySetInnerHTML`, which **strips `<script>` tags**. To run JavaScript:
```python
import streamlit.components.v1 as components
components.html("<script>...</script>", height=0)
```
This renders in a sandboxed iframe on the same localhost origin. Scripts access the parent page via `window.parent.document`. Used exclusively for the Doraemon widget.

---

## 8. Agent System

### 7 Agents Summary

| Agent | Key | Type | Context Used | Primary Behavior |
|---|---|---|---|---|
| Career Coach | `coach` | Global | Profile + all jobs + tracker + calendar | Diagnose → Pattern recognition → 2-3 options → Action plan |
| Resume Reviewer | `resume` | Per-job | Profile + selected job JD + **Project Library** | 5-step review: scan → diagnose → bullets → prioritize → rewrite |
| Gap Identifier | `gap` | Per-job | Profile + selected job JD | Strengths / Critical gaps / Minor gaps / Fit score |
| Interview Coach | `interview` | Per-job | Profile + selected job JD | Role-specific questions, rubric feedback, pressure simulation |
| Study Planner | `study` | Per-job | Profile + selected job JD + active JDs | 🔴/🟡/🟢 classification + resources + weekly schedule |
| Study Partner | `partner` | Global | Profile + all targets | WHY→Intuition→System→Detail→Trade-offs→Answer→Project→Code |
| Resume Synthesizer | `synthesizer` | Global | Profile + all JDs + all resume conversations | Cross-JD pattern synthesis, generalized resume strategy |

**Per-job agents** (resume, gap, interview, study): each has an independent conversation history per job. A dropdown at the top of the agent page lets the user select which tracked job (must have a JD) to work on.

**Global agents** (coach, partner, synthesizer): single conversation history shared across all sessions.

### Request / Response Flow
```
User types in text_area → clicks Send
    → message appended to conversations[agent_key][str(job_id)]  (per-job)
       or conversations[agent_key]                               (global)
    → db_save("conversations", ...)
    → st.rerun()
    → page re-renders, detects last message is "user"
    → get_system_prompt(agent_key, job=prep_job) builds prompt from live state
    → call_claude(messages, system)  OR  call_claude_with_tools(...)  [Coach + Calendar]
    → response appended to conversations
    → db_save("conversations", ...)
    → st.rerun()
```

**Key property:** System prompts are **built at call time** from live `session_state`. Agents always see current data — no manual sync needed.

### API Calls
```python
def call_claude(messages, system, max_tokens=2400) -> str:
    # Standard call with auto-continuation for long responses (up to 3 continuations)
    # Uses CONTINUE_PROMPT if stop_reason == "max_tokens"

def call_claude_with_tools(messages, system, tools, max_tokens=2400) -> str:
    # Used by Career Coach when Google Calendar is connected
    # Handles tool_use / tool_result turn cycle

def extract_project_with_claude(raw_text, title_hint="") -> dict:
    # Uses claude-haiku-4-5 for speed and cost efficiency
    # Returns structured JSON: title, technologies, metrics, contributions, challenges, summary
    # Strict prompt: never invent facts, metrics must be explicitly in text
```

### Context Injection in `get_system_prompt`
```python
def get_system_prompt(agent: str, job: dict | None = None) -> str:
    p  = st.session_state.profile
    jobs = st.session_state.jobs

    # Available to all agents:
    jobs_summary    # All jobs: company | role | status | date
    active_jobs     # status in (applied, screen, interview)
    active_jds      # JDs from active jobs

    # For per-job agents — from the passed `job` dict:
    recent_jd       # job["jd"]
    recent_company  # job["company"]
    recent_role     # job["role"]

    # Resume agent additionally gets:
    project_ctx = build_project_context_for_resume()
    # Formatted block of all projects injected before the 5-step framework
```

---

## 9. Agent System Prompts — Design Decisions

### Career Coach
- Reads the **full job tracker** — all companies, roles, statuses, dates, notes
- Framework strictly enforced: Diagnose → Pattern recognition → Options (A/B/C) → Action plan → Accountability
- Never gives generic advice — ties everything to actual job names in the tracker
- Thinks in 3 problem types: skills gap / strategy problem / execution problem
- When Calendar is connected: checks availability before scheduling, uses `create_calendar_event` proactively when suggesting action plans

### Resume Reviewer
- Uses the **selected job's JD** (not implicit most-recent — user picks from dropdown)
- Injects the full **Project Library** as a context block before its framework
- Framework: 10-sec scan → diagnose root cause → bullet structure (ACTION+WHAT+HOW+IMPACT) → top 3 priorities → Before/After rewrites
- Goal is interview probability, not grammar
- If no projects in library: shows a warning prompt inside the system prompt so the agent tells the user to add projects for better results
- **Anti-hallucination rule** in prompt: "if a metric or technology is NOT in the Project Library, do NOT invent it — use [X%] / [N users] placeholders"

### Gap Identifier
- Same per-job JD source as Resume Reviewer
- Required output: ✅ Strengths / ❌ Critical gaps / ⚠️ Minor gaps / 📊 Fit score (4 sub-scores) / 🎯 Recommendations
- Must always end: "The single most important thing to fix is: ___"

### Interview Coach
- Becomes an interviewer AT the specific company for the specific role
- One question at a time, real silence tolerance, follow-up probes
- Feedback format: ✅ What worked / ⚠️ What needs work / 🚀 How to fix it
- Spots behavioral patterns across answers, not just individual mistakes
- Calibrates difficulty to slightly above the candidate's current level

### Study Planner
**Learning style is hardcoded — not a user-configurable field.** The user's learning approach is baked directly into the system prompt:
- Builder-strategist: learns by producing, not consuming
- 3-layer system: Understand → Structure → APPLY (never stop at layer 2)
- Output-first notes: Intuition → System View → Trade-offs → Interview Answer → Code
- High ROI focus, question banks over passive notes, mistake log mindset

### Study Partner
**Teaching sequence is hardcoded (8 steps):**
1. WHY it exists (30 sec, no jargon)
2. Intuition/Analogy (before any technical detail)
3. System View (where does it fit)
4. Technical Detail
5. Trade-offs (pros/cons, when to use vs not)
6. Interview Answer (30-second version)
7. Project Connection (specific to user's known projects)
8. Code Snippet (last, small, annotated)

Dynamic adaptation: if "I get it" too fast → probe; if lost → return to analogy not more detail.

### Resume Synthesizer
- Reads **all JDs** stored across all tracked jobs
- Reads **all Resume Reviewer conversation histories** as signals (what was flagged per company)
- 4-step synthesis: extract requirements per JD → find patterns → synthesize generalized strategy per category → apply to each company
- Produces: universal resume version + company-specific variant advice
- Designed to surface patterns the user can't see by looking at one JD at a time

---

## 10. Project Library — Architecture & Agent Integration

### Purpose
Prevent the Resume Reviewer from hallucinating or underestimating experience. The library gives it verified ground truth: exact technologies used, real metrics, first-person contributions, and challenges solved — extracted directly from project reports.

### Upload Pipeline
```
User uploads file (PDF / DOCX / Markdown / Text)
    → read_pdf_bytes()    OR
       read_docx_bytes()  OR
       direct decode      (for .md, .txt, pasted text)
    → raw_content (str, capped at 60,000 chars for DB)
    → extract_project_with_claude(raw_content, title_hint)
        → claude-haiku-4-5 with strict JSON extraction prompt
        → returns: title, technologies[], metrics[], contributions, challenges, summary
    → db_save_project(title, source_type, raw_content, extracted)
    → st.rerun() — project appears in library
```

### File Extraction

**PDF** (`read_pdf_bytes`):
- Uses `pypdf.PdfReader` to extract text page by page
- Returns joined page text

**DOCX** (`read_docx_bytes`):
- **Primary:** `python-docx` — extracts paragraphs and table rows (cells joined with ` | `)
- **Fallback:** pure stdlib — opens `.docx` as a ZIP archive, parses `word/document.xml` with `xml.etree.ElementTree`, extracts `<w:t>` elements grouped by `<w:p>` paragraphs
- Fallback exists because `python-docx` may not be in the running Streamlit environment if not restarted after install. The fallback has no external dependencies.

**Markdown / Text:** Direct `bytes.decode("utf-8", errors="replace")`

### Extraction Prompt Design
Claude Haiku is given the raw text and asked to return a JSON object. Key constraints in the prompt:
- `metrics`: **only** copy exact numbers/percentages from the text — empty array if none exist
- `contributions`: first-person, past tense, ownership-focused
- Return only valid JSON — no markdown fences
- Never add facts not in the source text

Post-processing: regex `re.search(r'\{.*\}', text, re.DOTALL)` extracts the JSON object even if the model adds any surrounding text. Falls back to a basic dict if parsing fails.

### Agent Integration — Resume Reviewer
```python
def build_project_context_for_resume() -> str:
    projects = db_get_projects()
    # Formats all projects into a labeled block:
    # ━━━ PROJECT LIBRARY ━━━
    # INSTRUCTION: auto-match to JD, use real facts, [X%] if no real number
    # ▸ PROJECT: [title]
    #   Technologies : ...
    #   Metrics      : ...
    #   Contributions: ...
    #   Challenges   : ...
    #   Summary      : ...
    # ━━━ END PROJECT LIBRARY ━━━
```

This block is injected into the Resume Reviewer system prompt at every call. The agent sees it as ground truth and is explicitly told to match projects to the JD automatically.

### Project Library Page UI
- **Add New Project** expander (auto-expanded when library is empty):
  - 4 tabs: PDF | Word (.docx) | Markdown / Text | Paste / Type
  - Optional title hint field
  - "Extract & Add to Library" button — disabled until content is loaded
  - Post-extraction preview card showing detected tech, metrics, contributions
- **Library display** — one expander per project:
  - Header: source icon + title + date added
  - Body: tech stack badges (lime), metrics list, contributions, challenges, summary
  - Delete button per project
- **Status bar** at top: project count · total technologies indexed · total metrics captured
- **Info footer** explaining how the library powers the Resume Reviewer

---

## 11. Google Calendar Integration

### Authentication
OAuth2 flow via `google-auth-oauthlib`. Credentials stored in `google_credentials.json` (in the project directory, gitignored). Connection state stored in the `kv` DB table under key `"google_calendar_credentials"`.

```python
def connect_calendar_oauth() -> tuple[bool, str]  # Opens browser, runs OAuth flow
def disconnect_calendar()                          # Clears credentials from DB + file
def is_calendar_connected() -> bool               # Checks for valid credentials
def get_calendar_credentials()                     # Returns google.oauth2 Credentials object
```

### Tool Definitions (passed to Career Coach only)
```python
CALENDAR_TOOLS = [
    get_calendar_events,   # Lists events in a date range
    create_calendar_event  # Creates new event with title, date, time, duration, description
]
```

### Routing
When the Career Coach agent makes an API call and calendar is connected, `call_claude_with_tools()` is used instead of `call_claude()`. The function handles the full tool-use cycle: sends tools to Claude, receives `tool_use` blocks, executes the tool call, appends `tool_result`, continues until `stop_reason != "tool_use"`.

---

## 12. Routing & Navigation

Streamlit has no built-in router. Navigation is managed via `st.session_state.current_page` and `st.session_state.current_agent`.

```python
# Navigation pattern (sidebar)
if st.button("📚  Project Library"):
    st.session_state.current_page = "project_library"
    st.rerun()

# Page rendering — if/elif chain at bottom of file
if   st.session_state.current_page == "dashboard":        render_dashboard()
elif st.session_state.current_page == "tracker":          render_tracker()
elif st.session_state.current_page == "add_job":          render_add_job()
elif st.session_state.current_page == "agents":           render_agents()
elif st.session_state.current_page == "profile":          render_profile()
elif st.session_state.current_page == "project_library":  render_project_library()
```

### Pages
| Page key | Description |
|---|---|
| `dashboard` | Pipeline stats (5 metrics), recent applications, quick coach insight |
| `tracker` | Kanban view tabbed by status, job cards with inline status badges |
| `add_job` | 3-tab form: Details / Progress / Notes & JD — used for both add and edit |
| `agents` | Chat interface; `current_agent` selects which of 7 agents is active; per-job agents show a job dropdown |
| `profile` | Name, role, resume (textarea), goals, Google Calendar connect/disconnect |
| `project_library` | Upload reports, manage project knowledge base |

---

## 13. Job Tracker — CRUD & Status Flow

### Status pipeline
```
wishlist → applied → screen → interview → offer
                                        ↘ rejected (any stage)
```

### CRUD Functions
```python
def add_job(job_data: dict) -> None       # Assigns id, created_at, empty progress; db_save
def update_job(job_id, updates) -> None   # Merges updates into job dict; db_save
def delete_job(job_id) -> None            # Filters out by id; db_save
def get_job(job_id) -> dict | None        # Linear search (fine at current scale)
def get_jobs() -> list[dict]              # Returns session_state.jobs directly
def job_stats() -> tuple                  # total, active, interviews, offers, rate string
```

### Progress Timeline
Each job has `progress: list[ProgressNote]`. Notes are attached to a stage and displayed in stage-order. Notes survive status changes — a note from "Applied" remains visible at "Interview". Timeline is rendered as a custom HTML component in the job detail view.

### Per-job Agent Selection
`st.session_state.prep_job_id` tracks which job is selected for per-job agents. The agent page shows a dropdown of all jobs that have a JD pasted. Conversations are stored per job_id so switching jobs switches the chat history cleanly.

---

## 14. API Key Handling

**Not persisted to DB.** Load order:
1. `os.environ.get('ANTHROPIC_API_KEY', '')`
2. `st.secrets.get('ANTHROPIC_API_KEY', '')` (Streamlit Cloud)
3. Falls back to empty string → agent calls return a warning message

```python
def _read_env_api_key() -> str     # Handles both sources + strips quotes
def _looks_like_anthropic_key(k)   # Returns True if key starts with "sk-ant-"
def get_client()                   # Returns anthropic.Anthropic(api_key=...) or error sentinel
```

`get_client()` returns either a valid client, the string `"invalid_format"`, or `None`. All `call_claude*` functions check this and return user-friendly warning strings rather than raising exceptions.

---

## 15. Companion Widget (Doraemon)

A floating animated Doraemon avatar that persists across all pages.

### Architecture
```
st.markdown(CSS + HTML div)   → renders the widget structure and CSS animations
                                 (CSS-only animations work fine here)

components.v1.html(JS, height=0)  → runs JavaScript that:
                                    - finds the HTML elements via window.parent.document
                                    - sets up drag (mousedown/mousemove/mouseup)
                                    - sets up click detection (no-move mousedown+up)
                                    - shows random messages in the bubble
                                    - spawns particle bursts on click
                                    - auto-rotates idle messages every 14s
```

**Why `components.v1.html` for JS:** `st.markdown` passes HTML through React's `dangerouslySetInnerHTML` which strips all `<script>` tags. `components.v1.html` creates an iframe on the same localhost origin, so `window.parent.document` gives full DOM access.

### Features
- **Persistent fixed position** — bottom-right corner, `z-index: 9999`, visible on all pages
- **Draggable** — mousedown + mousemove on `window.parent.document`; clamped to viewport bounds; distinguishes drag vs click by movement threshold (>4px = drag)
- **Click interaction** — bounce animation (`scale(1.28) rotate(-6deg)` → settle), smile widens temporarily, 6 staggered emoji particles fly out
- **Random encouragements** — 13 messages, no immediate repeats
- **Auto-rotate** — idle bubble refreshes every 14 seconds with 6 ambient messages
- **CSS animations** — bob (translateY -10px loop), blink (scaleY 0.06), tail wag (rotate ±12°), bell shine (opacity pulse)
- **Touch support** — `touchstart/touchmove/touchend` handlers for drag and tap

---

## 16. Known Limitations of Current System

### Agent isolation (primary architectural gap)
Each agent has an isolated conversation history. **Agents cannot see what other agents found.** The Interview Coach's weak-area findings don't flow to the Study Planner. The Career Coach reads the job tracker but not agent outputs. This is the core problem the multi-agent redesign solves.

### Project Library is Resume-only
Project data is currently only injected into the Resume Reviewer. The Gap Identifier, Interview Coach, and Study Planner would all benefit from knowing the user's actual project experience — especially for realistic fit scoring and targeted study plans. This is a planned extension.

### Conversation history grows unbounded
No summarization or truncation. Very long chats will eventually hit context limits and increase cost. Mitigation plan: summarize-then-truncate when conversation exceeds ~20 turns.

### Streamlit re-run performance
Every interaction triggers a full script re-run (~2,200 lines). The DB query for project count runs on every sidebar render. Low impact now but worth batching as the app grows. `st.fragment` (Streamlit 1.37+) can isolate the chat area to avoid full re-renders.

### Single-user only
Local SQLite file, no auth. Intentional for personal-use phase.

### Google Calendar token expiry
OAuth tokens expire and require re-authorization. No automatic token refresh is implemented — the user must reconnect via the Profile page when this happens.

---

## 17. Future Architecture — Multi-Agent System

### The core problem to solve
The current system is **7 isolated chatbots**. The target architecture is a **coordinated agent graph** where:
- The Career Coach acts as an **orchestrator** that routes to sub-agents
- Sub-agents **write findings to shared state**
- Weak areas found in interviews **automatically seed** the Study Planner
- The Project Library is **queryable by all agents**, not just Resume Reviewer
- The system can **flag patterns and trigger actions** without being asked

### Planned LangGraph State Schema
```python
from typing import TypedDict, Annotated
import operator

class CareerOSState(TypedDict):
    # Input
    user_message: str

    # Read-only context (loaded from DB at graph entry)
    profile: dict
    jobs: list
    projects: list           # Full Project Library — all agents can query this

    # Agent findings — written by sub-agents, read by orchestrator + other agents
    gap_findings: str              # written by GapAgent
    weak_areas: list[str]          # written by InterviewAgent → read by StudyAgent
    resume_suggestions: str        # written by ResumeAgent
    matched_projects: list[dict]   # written by ProjectMatcherNode → read by ResumeAgent
    study_plan: str                # written by StudyAgent

    # Orchestrator outputs
    coach_diagnosis: str           # "skills_gap" | "strategy" | "execution" | "interview_prep"
    action_plan: str
    next_steps: list[str]

    # Accumulated message history (all agents contribute)
    messages: Annotated[list, operator.add]
```

### Planned Graph Structure
```
User input
    → OrchestratorNode (Career Coach)
          ↓ conditional routing based on diagnosis
    ┌─────┴──────────────────────────────┐
    │                                    │
GapNode              ResumeNode ← ProjectMatcherNode (queries Project Library)
InterviewNode        SynthesizerNode
    │                                    │
    └─────────────────────────────────────┘
          ↓ findings written to shared state
    SynthesisNode (Coach reads all findings, produces action plan)
          ↓
    User response
```

### ProjectMatcherNode (new in v2)
A dedicated node that, given a JD, queries the Project Library and scores each project for relevance. Returns a ranked list of matching projects with per-field highlights. This replaces the current "inject all projects" approach with a targeted retrieval step.

```python
def project_matcher_node(state: CareerOSState) -> CareerOSState:
    jd = state["jobs"][0]["jd"]  # selected job
    projects = state["projects"]
    # Score each project against JD using embedding similarity or keyword overlap
    # Return top-3 ranked projects
    state["matched_projects"] = rank_projects(projects, jd)
    return state
```

### Conditional Routing Logic
```python
def route_after_diagnosis(state: CareerOSState) -> list[str]:
    d = state["coach_diagnosis"]
    if d == "skills_gap":
        return ["gap_node", "study_node"]          # parallel
    elif d == "execution":
        return ["resume_node", "project_matcher"]  # parallel
    elif d == "interview_prep":
        return ["interview_node", "study_node"]
    elif d == "strategy":
        return ["synthesizer_node"]
    return ["synthesis_node"]
```

### Persistence for LangGraph
```python
from langgraph.checkpoint.sqlite import SqliteSaver
checkpointer = SqliteSaver.from_conn_string("careeros.db")
# Adds a 'checkpoints' table to the existing DB
# Replaces all manual db_save calls with automatic checkpoint writes
app = graph.compile(checkpointer=checkpointer)
```

### Cross-Agent Data Flows (target)
| Source agent | Data written | Consuming agent |
|---|---|---|
| InterviewAgent | `weak_areas: ["system design", "SQL window functions"]` | StudyAgent builds targeted plan |
| GapAgent | `gap_findings` with critical gap list | Coach surfaces in action plan |
| ResumeAgent | `resume_suggestions` per company | SynthesizerAgent finds patterns |
| ProjectMatcherNode | `matched_projects` ranked list | ResumeAgent rewrites with verified facts |
| Coach diagnosis | `coach_diagnosis` | Routing function selects sub-agents |

### Implementation Order
1. Keep using current system until ~10 jobs + JDs + real interview data accumulated
2. Introduce `CareerOSState` TypedDict mirroring current `session_state`
3. Wrap current `get_system_prompt` functions as LangGraph node functions
4. Add `ProjectMatcherNode` — first new node not in current system
5. Wire `InterviewAgent → weak_areas → StudyAgent` (highest value cross-agent flow)
6. Add orchestrator routing node (Career Coach decides which agents to call)
7. Replace `db_save` calls with LangGraph checkpoint writes
8. Add tool use: web search (job research), file generation (download resume DOCX), calendar for all agents

### Data Being Collected Now (valuable for v2)
- Gap findings per company → seeds study topic list automatically
- Weak areas from mock interviews → triggers targeted study sessions
- Which resume bullets get rewritten most → signals what the current resume is weak at
- Response rates by company type → Coach diagnoses targeting strategy
- Project metrics and tech stack → ProjectMatcherNode training signal

---

## 18. Design Decisions Log

| Decision | Rationale |
|---|---|
| Single `app.py` file | Streamlit re-runs the whole script; modules add complexity with no current benefit |
| SQLite over cloud DB | Local-first, zero setup, data stays on machine; same file used by future LangGraph checkpointer |
| Two SQLite tables (`kv` + `projects`) | Projects have structured fields (arrays, typed columns) that don't fit cleanly in the JSON blob pattern of `kv` |
| `db_load_all()` on startup, then `_db_loaded` flag | One query at startup vs re-loading on every interaction; flag is the correct Streamlit idiom |
| API key not persisted | Security — key comes from environment, never stored in user-readable DB |
| Per-job agent conversations | Independent history per job prevents contamination; user can have a resume review for Company A and Company B simultaneously without context bleed |
| `prep_job_id` for per-job agent selection | Explicit user choice is more reliable than "most recently added job with a JD" implicit heuristic |
| `claude-opus-4-5` for chat agents | Quality over cost for a personal daily-use tool |
| `claude-haiku-4-5` for extraction | Project extraction is a structured JSON task — Haiku is fast, cheap, and accurate enough; saves cost on every upload |
| DOCX stdlib fallback | `python-docx` may not be in the live Streamlit process if installed after app start; stdlib `zipfile` + `xml.etree` always works with no restart |
| Learning style hardcoded in study agents | User provided detailed learning guides; baking them in is more reliable than user re-entering them; they also shouldn't change often |
| `components.v1.html(height=0)` for JS | `st.markdown` strips `<script>` tags via React's `dangerouslySetInnerHTML`; iframe on same origin with `window.parent.document` is the correct Streamlit pattern |
| Project Library injected into Resume Reviewer only (currently) | Resume rewriting has highest hallucination risk; other agents benefit less from exact project facts in their current form |
| `build_project_context_for_resume()` injects all projects | Avoids an extra API call for pre-filtering; Claude is instructed to auto-match; acceptable until project count grows large (>20) |
| `resize: vertical` on all textareas | Users frequently need to write/read multi-line content (resumes, JDs, project descriptions); the constraint was CSS-only, no logic change |
| Doraemon widget as floating overlay | Companion presence improves sustained usage motivation; implemented as a non-intrusive fixed overlay that doesn't interfere with any page layout |
| Conversations not cleared on profile update | Profile changes should affect future prompts only; existing conversation history remains valid as context |
