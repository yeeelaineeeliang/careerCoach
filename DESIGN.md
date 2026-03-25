# CareerOS — Design & Architecture Documentation

> **Purpose of this document:** Complete reference for the current system design, code structure, agent behavior, data model, and planned future architecture. Use this as the starting context for any new implementation session.

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
10. [Routing & Navigation](#10-routing--navigation)
11. [Job Tracker — CRUD & Status Flow](#11-job-tracker--crud--status-flow)
12. [API Key Handling](#12-api-key-handling)
13. [Known Limitations of Current System](#13-known-limitations-of-current-system)
14. [Future Architecture — LangGraph Multi-Agent](#14-future-architecture--langgraph-multi-agent)
15. [Design Decisions Log](#15-design-decisions-log)

---

## 1. System Overview

CareerOS is a single-file Streamlit application that combines:

- A **Kanban job tracker** (6 status columns, per-job progress timeline, JD storage)
- A **dashboard** with live pipeline stats and on-demand Career Coach insight
- **6 specialized AI agents** each powered by Claude with deeply personalized system prompts
- **SQLite persistence** so all data survives restarts

The system is designed around one core idea: **agents should be useful because they have context, not because the user re-explains themselves every session.** Profile, job tracker data, and JDs are all injected into every agent's system prompt at call time.

### What it is NOT yet
- A true multi-agent system (agents don't share findings with each other)
- An agentic loop (no tool use, no agent-to-agent calls)
- A LangGraph graph (planned — see Section 14)

---

## 2. File Structure

```
careeros/
├── app.py           # Entire application — single file
├── requirements.txt # streamlit>=1.35.0, anthropic>=0.28.0
├── careeros.db      # SQLite database (auto-created on first run, gitignore this)
└── DESIGN.md        # This document
```

**Why single file:** Streamlit's execution model re-runs the entire script on every interaction. Splitting into modules is possible but adds import complexity with no current benefit given the app's size (~1,100 lines).

---

## 3. Tech Stack

| Layer | Technology | Notes |
|---|---|---|
| UI framework | Streamlit 1.35+ | `st.session_state` for in-memory state, `st.rerun()` for re-renders |
| LLM | Anthropic Claude (`claude-opus-4-5`) | All 6 agents use the same model |
| Persistence | SQLite3 (stdlib) | Single `kv` table, key-value JSON store |
| Styling | Custom CSS injected via `st.markdown` | Dark theme, Syne + IBM Plex Mono fonts |
| Fonts | Google Fonts CDN | Syne (headings/UI), IBM Plex Mono (labels/code) |
| Python | 3.12+ | Uses `pathlib.Path`, `datetime`, `typing.Optional` |

---

## 4. Data Model

All data is stored as JSON in SQLite. The schema is flat key-value — no relational tables.

### 4.1 Profile
```python
{
    "name": str,        # e.g. "Annie Chen"
    "role": str,        # e.g. "ML Engineer"
    "resume": str,      # Full resume text, pasted plain text
    "goals": str        # Free-form current situation + objectives
}
```
**DB key:** `"profile"`

### 4.2 Job
Each job is a dict in the `jobs` list:
```python
{
    "id": int,                    # Auto-incrementing, never reused
    "company": str,               # Required
    "role": str,
    "status": str,                # One of: wishlist|applied|screen|interview|offer|rejected
    "date": str,                  # ISO date string "YYYY-MM-DD"
    "location": str,
    "salary": str,                # Free text e.g. "$120k–$160k"
    "url": str,                   # Job posting URL
    "tags": list[str],            # e.g. ["ML", "Python", "startup"]
    "jd": str,                    # Full job description — CRITICAL for agents
    "notes": str,                 # Personal notes (not shown to agents directly)
    "progress": list[ProgressNote],
    "created_at": float           # Unix timestamp, used for sorting
}
```

### 4.3 ProgressNote
```python
{
    "status": str,   # Which stage this note is attached to
    "note": str,     # The note text
    "date": str      # ISO date string "YYYY-MM-DD"
}
```

### 4.4 Conversations
```python
{
    "coach":     list[Message],
    "resume":    list[Message],
    "gap":       list[Message],
    "interview": list[Message],
    "study":     list[Message],
    "partner":   list[Message]
}
```

### 4.5 Message
```python
{
    "role":    "user" | "assistant",
    "content": str
}
```
This format matches the Anthropic API messages format exactly — no transformation needed before API calls.

### 4.6 Status Enum
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
```sql
CREATE TABLE IF NOT EXISTS kv (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
```
Four rows at steady state: `profile`, `jobs`, `next_job_id`, `conversations`.

### Core Functions
```python
DB_PATH = Path(__file__).parent / "careeros.db"

def _db() -> sqlite3.Connection
    # Opens connection, ensures table exists, returns connection

def db_save(key: str, value: any) -> None
    # INSERT OR REPLACE — overwrites entire value for key
    # Uses json.dumps(value, default=str) to handle datetime objects

def db_load(key: str, default=None) -> any
    # Returns parsed JSON or default if key not found

def db_load_all() -> dict
    # Reads all rows in one query — used at startup only
```

### Save Points
Every mutation immediately calls `db_save`. There is no batch/delayed write.

| Action | db_save calls |
|---|---|
| `add_job()` | `db_save("jobs", ...)` + `db_save("next_job_id", ...)` |
| `update_job()` | `db_save("jobs", ...)` |
| `delete_job()` | `db_save("jobs", ...)` |
| Profile save button | `db_save("profile", ...)` |
| Agent sends/receives message | `db_save("conversations", ...)` |
| Clear chat button | `db_save("conversations", ...)` |
| Starter chip clicked | `db_save("conversations", ...)` |

### Startup Load
```python
if "_db_loaded" not in st.session_state:
    saved = db_load_all()
    st.session_state.profile = saved.get("profile", {...defaults})
    st.session_state.jobs = saved.get("jobs", [])
    st.session_state.next_job_id = saved.get("next_job_id", 1)
    st.session_state.conversations = saved.get("conversations", {...defaults})
    st.session_state._db_loaded = True
```
The `_db_loaded` flag prevents re-loading from DB on every Streamlit re-run (which happens on every user interaction).

---

## 6. Session State

### Persisted (survives restart via SQLite)
| Key | Type | Description |
|---|---|---|
| `profile` | dict | User's name, role, resume, goals |
| `jobs` | list[dict] | All job applications |
| `next_job_id` | int | Auto-increment counter |
| `conversations` | dict | Chat histories for all 6 agents |

### UI-only (reset on restart, intentional)
| Key | Type | Description |
|---|---|---|
| `api_key` | str | Loaded from env var, not persisted (security) |
| `current_page` | str | Active view: dashboard/tracker/add_job/agents/profile |
| `current_agent` | str | Active agent tab: coach/resume/gap/interview/study/partner |
| `selected_job_id` | int\|None | Currently viewed job |
| `editing_job_id` | int\|None | Job being edited in add_job view |
| `_db_loaded` | bool | Guard flag — prevents re-loading DB every re-run |

---

## 7. UI Architecture

### Layout
```
Streamlit wide layout
├── Sidebar (always visible)
│   ├── Logo + subtitle
│   ├── Nav: Overview section (Dashboard, Job Tracker)
│   ├── Nav: AI Agents section (6 agent buttons)
│   ├── Nav: Settings (My Profile)
│   └── Mini stats bar (applied · active · interviews · offers · rate)
└── Main content area (page-routed, see Section 10)
    ├── Dashboard
    ├── Job Tracker (Kanban)
    ├── Add/Edit Job (3-tab form)
    ├── Agents (chat interface)
    └── Profile
```

### Styling Approach
All styling is injected as a single `<style>` block via `st.markdown(..., unsafe_allow_html=True)` at the top of the file.

**Color palette:**
```
Background:   #080910  (near-black)
Surface 1:    #0f1015  (sidebar)
Surface 2:    #161720  (cards, inputs)
Surface 3:    #1e2030  (user messages)
Accent lime:  #c5f135  (primary CTA, active states, headings)
Accent sky:   #5bc8f5  (applied status, info)
Accent amber: #f5c35b  (screen status, warnings)
Accent violet:#a55bf5  (interview status)
Accent rose:  #f55b7a  (rejected status, errors)
Text primary: #eeedf0
Text muted:   #7a7a8c
Text dimmer:  #555568
```

**Font override issue (fixed):** Streamlit renders button labels inside `<p>` tags. The global rule `body, .main, p, span, label, div { color: #eeedf0 !important; }` overrides button text color. Fix:
```css
.stButton > button p,
.stButton > button span,
.stButton > button div {
    color: #080910 !important;
}
```

**Custom HTML components:** Job cards, status badges, chat messages, the context status bar, and the progress timeline are all rendered via `st.markdown(..., unsafe_allow_html=True)` with inline CSS classes defined in the style block.

---

## 8. Agent System

### Architecture (Current)
```
User message
    → appended to st.session_state.conversations[agent_key]
    → db_save("conversations", ...)
    → st.rerun()
    → page re-renders, detects last message is from user
    → get_system_prompt(agent_key) builds prompt from live state
    → call_claude(messages, system) → Anthropic API
    → response appended to conversations[agent_key]
    → db_save("conversations", ...)
    → st.rerun()
```

**Key architectural property:** System prompts are **dynamically built at call time** from live `session_state`. This means the Career Coach always sees your current job list, the Resume agent always uses your most recent JD, and the Gap agent always reflects your latest profile — without any manual refresh.

### Agent Context Injection
```python
def get_system_prompt(agent: str) -> str:
    p = st.session_state.profile
    jobs = st.session_state.jobs

    # Pre-computed context available to all agents:
    jobs_summary      # All jobs: company | role | status | date | notes
    active_jobs       # Jobs with status in (applied, screen, interview)
    active_jds        # JDs from active jobs, joined with ---
    recent_jd_job     # Most recently created job that has a JD
    recent_jd         # That job's JD text
    recent_company    # That job's company
    recent_role       # That job's role
```

### API Call
```python
def call_claude(messages: list, system: str, max_tokens: int = 1200) -> str:
    client = anthropic.Anthropic(api_key=st.session_state.api_key)
    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1200,
        system=system,
        messages=messages  # Full conversation history, Anthropic format
    )
    return response.content[0].text
```

### 6 Agents Summary

| Agent | Key | Context Used | Primary Behavior |
|---|---|---|---|
| Career Coach | `coach` | profile + all jobs + full tracker | Diagnose → Pattern recognition → 2-3 options → Action plan |
| Resume Reviewer | `resume` | profile.resume + most recent JD | 5-step review: scan → diagnose → bullets → prioritize → rewrite |
| Gap Identifier | `gap` | profile.resume + most recent JD | ✅ Strengths / ❌ Critical gaps / ⚠️ Minor gaps / 📊 Fit score |
| Interview Coach | `interview` | profile.resume + most recent JD | Role-specific questions, rubric feedback, pressure simulation |
| Study Planner | `study` | profile + active jobs + active JDs | 🔴/🟡/🟢 classification + resources + weekly schedule |
| Study Partner | `partner` | profile + all job targets | WHY→Intuition→System→Detail→Trade-offs→Interview Answer→Project→Code |

---

## 9. Agent System Prompts — Design Decisions

### Career Coach
- Has access to the **full job tracker** (all companies, roles, statuses, dates, notes)
- Follows a strict framework: Diagnose first → Pattern recognition → Options over commands → Action plans → Accountability
- **Never gives generic advice** — must tie everything to actual job names in the tracker
- Thinks in 3 problem types: skills gap / strategy problem / execution problem

### Resume Reviewer
- Uses `recent_jd_job` (most recently created job with a JD pasted)
- Framework: 10-sec scan → diagnose root cause → bullet structure (ACTION+WHAT+HOW+IMPACT) → top 3 priorities → Before/After rewrites
- Goal is **interview probability**, not grammar

### Gap Identifier
- Same JD source as Resume Reviewer
- Required to output a structured fit score broken into: Technical Match / Experience Level / Project Signal / Keywords
- Must always end with "The single most important thing to fix is: ___"

### Interview Coach
- Becomes an interviewer AT the specific company for the specific role
- One question at a time, no interrupting, follow-up probes
- Feedback format: ✅ What worked / ⚠️ What needs work / 🚀 How to fix it
- Spots behavioral patterns across answers, not just individual mistakes

### Study Planner
**Learning style is hardcoded — not a user-configurable field.** The user provided detailed guides about their learning style; these are baked directly into the prompt:
- Builder-strategist learner: learns by producing, not consuming
- 3-layer system: Understand → Structure → APPLY
- Output-first notes: Intuition → System View → Trade-offs → Interview Answer → Code
- High ROI focus, question banks over passive notes

### Study Partner
**Teaching sequence is hardcoded:**
1. WHY it exists (30 sec, no jargon)
2. Intuition/Analogy (before any technical detail)
3. System View (where does it fit in the bigger picture)
4. Technical Detail
5. Trade-offs
6. Interview Answer (30-second version)
7. Project Connection (fraud system / RAG pipeline / CalPin)
8. Code Snippet (last, only after the above)

Dynamic adaptation: if user says "I get it" too fast → probe; if lost → return to analogy not more detail.

---

## 10. Routing & Navigation

Streamlit has no real router. Navigation is managed via `st.session_state.current_page`:

```python
# Navigation pattern
if st.button("Dashboard"):
    st.session_state.current_page = "dashboard"
    st.rerun()

# Page rendering — if/elif chain at bottom of file
if st.session_state.current_page == "dashboard":
    render_dashboard()
elif st.session_state.current_page == "tracker":
    render_tracker()
elif st.session_state.current_page == "add_job":
    render_add_job()
elif st.session_state.current_page == "agents":
    render_agents()
elif st.session_state.current_page == "profile":
    render_profile()
```

**Pages:**
- `dashboard` — stats + recent applications + coach insight
- `tracker` — Kanban view, tabbed by status
- `add_job` — 3-tab form (Details / Progress / Notes & JD), used for both add and edit
- `agents` — chat interface, `current_agent` selects which of 6 agents is active
- `profile` — name, role, resume, goals

---

## 11. Job Tracker — CRUD & Status Flow

### Status pipeline
```
wishlist → applied → screen → interview → offer
                                        ↘ rejected (can happen at any stage)
```

### CRUD Functions
```python
def add_job(job_data: dict) -> None
    # Assigns id, created_at, empty progress list
    # Saves to session_state.jobs + db_save

def update_job(job_id: int, updates: dict) -> None
    # Merges updates into existing job dict
    # db_save

def delete_job(job_id: int) -> None
    # Filters out job by id
    # db_save

def get_job(job_id: int) -> dict | None
    # Linear search — fine at current scale

def get_jobs() -> list[dict]
    # Returns st.session_state.jobs directly
```

### Progress Timeline
Each job has a `progress: list[ProgressNote]` field. Notes are attached to a specific status stage and displayed in the timeline in status-order. Notes survive status changes — a note added while "Applied" stays visible even after moving to "Interview".

### JD Storage
The job description is stored in `job["jd"]` (plain text). This is the most important field for agent quality. Agents use `recent_jd_job` (most recently created job that has a non-empty `jd`). **Future improvement:** let users select which job to "activate" for agent context instead of always using the most recent.

---

## 12. API Key Handling

**Not persisted to DB intentionally** (security).

Load order:
1. Check `os.environ.get('ANTHROPIC_API_KEY', '')`
2. Check `st.secrets.get('ANTHROPIC_API_KEY', '')` (for Streamlit Cloud)
3. Fall back to empty string (agent calls will return a warning message)

```python
# In init, after init_state():
if not st.session_state.api_key:
    env_key = os.environ.get('ANTHROPIC_API_KEY', '')
    if not env_key:
        try:
            env_key = st.secrets.get('ANTHROPIC_API_KEY', '')
        except Exception:
            env_key = ''
    if env_key:
        st.session_state.api_key = env_key
```

**Local setup:** `export ANTHROPIC_API_KEY="sk-ant-..."` in `~/.zshrc` or `~/.bashrc`

**Streamlit Cloud:** Add to app secrets as `ANTHROPIC_API_KEY = "sk-ant-..."`

The sidebar API key input field has been **removed**. The key is invisible to the user and loaded silently.

---

## 13. Known Limitations of Current System

These are the gaps to address in the next version:

### Agent isolation (biggest limitation)
Each agent has its own isolated conversation history. **Agents cannot see what other agents found.** If the Gap Identifier identifies "missing system design skills", the Interview Coach doesn't know that — you'd have to manually tell it. The Career Coach reads the job tracker but not agent outputs.

### JD selection is implicit
Agents always use the most recently created job that has a JD. There's no way to say "run gap analysis on THIS specific job." Users must be careful about which job they've added most recently.

### No agent-initiated actions
Agents can only respond to messages. They cannot:
- Flag a stale application automatically
- Trigger the Study Planner when Interview Coach finds a weak area
- Create a checklist item when the Coach recommends an action

### Single-user only
The SQLite file is local. No multi-user support. Not relevant for personal use but noted.

### Conversation history grows unbounded
No truncation or summarization of long conversations. Very long chats will eventually hit the Claude context window limit and cost more.

### Streamlit re-run model
Every button click triggers a full script re-run. This is fine for current complexity but can cause flicker on the chat view. Consider `st.fragment` (Streamlit 1.37+) for the chat area in future.

---

## 14. Future Architecture — LangGraph Multi-Agent

### The core problem to solve
The current system is **6 isolated chatbots**. The future system should be a **coordinated agent graph** where:
- The Career Coach acts as an **orchestrator node** that routes to sub-agents
- Sub-agents **write findings to shared state**
- The Coach **reads those findings** and synthesizes
- Weak areas found in interviews **automatically inform** the Study Planner
- The system can **flag patterns** without being asked

### Planned LangGraph State Schema
```python
from typing import TypedDict, Annotated
import operator

class CareerOSState(TypedDict):
    # Input
    user_message: str

    # Profile + tracker (read-only context)
    profile: dict
    jobs: list

    # Agent findings (written by sub-agents, read by orchestrator)
    gap_findings: str           # written by GapAgent
    weak_areas: list[str]       # written by InterviewAgent → read by StudyAgent
    resume_suggestions: str     # written by ResumeAgent
    study_plan: str             # written by StudyAgent

    # Orchestrator outputs
    coach_diagnosis: str        # "skills gap" | "strategy" | "execution"
    action_plan: str
    next_steps: list[str]

    # Accumulated message history (all agents contribute)
    messages: Annotated[list, operator.add]
```

### Planned Graph Structure
```
User input
    → Orchestrator (Career Coach)
          ↓ conditional routing based on diagnosis
    ┌─────┴──────────────────────────┐
    │                                │
GapAgent                      ResumeAgent
InterviewAgent                StudyAgent
    │                                │
    └─────────────────────────────────┘
          ↓ all write to shared state
    Synthesizer (Coach summarizes findings)
          ↓
    User response
```

### Conditional Routing Logic
```python
def route_after_diagnosis(state: CareerOSState) -> list[str]:
    diagnosis = state["coach_diagnosis"]
    if "skills gap" in diagnosis:
        return ["gap_agent", "study_agent"]    # parallel
    elif "execution" in diagnosis:
        return ["resume_agent"]
    elif "interview" in diagnosis:
        return ["interview_agent", "study_agent"]
    return ["synthesize"]
```

### Persistence for LangGraph
```python
from langgraph.checkpoint.sqlite import SqliteSaver
checkpointer = SqliteSaver.from_conn_string("careeros.db")
app = graph.compile(checkpointer=checkpointer)
```
LangGraph's checkpointer replaces the current manual `db_save` pattern and gives automatic state persistence + conversation threading.

### Data to collect now (for graph training)
While using the current system, the following data will be valuable:
- **Gap findings per company** → will seed Study Planner topic list automatically
- **Weak areas from mock interviews** → will trigger targeted study sessions
- **Which resume versions get callbacks** → Coach can spot patterns
- **Response rates by company type** → Coach diagnoses targeting strategy
- **Progress notes** → timeline of what works at each stage

### Recommended implementation order
1. Keep using current system until ~10 jobs tracked with JDs + real interview data
2. Introduce `AgentState` TypedDict mirroring current `session_state` structure
3. Wrap current `get_system_prompt` functions as LangGraph nodes
4. Add orchestrator node (Career Coach routing logic)
5. Wire shared state so findings flow between nodes
6. Replace `db_save` calls with LangGraph checkpoint writes
7. Add tool use: web search for job research, calendar for interview scheduling

---

## 15. Design Decisions Log

| Decision | Rationale |
|---|---|
| Single `app.py` file | Streamlit re-runs the whole script; modules add complexity with no current benefit |
| SQLite over Supabase/cloud DB | Local-first, zero setup, data stays on machine during active job search phase |
| `db_load_all()` on startup | One query vs 4 separate queries; `_db_loaded` flag prevents re-running on every interaction |
| API key not persisted | Security — key should come from environment, not be stored in a user-readable DB |
| Learning style removed from profile | The study guides were provided as coaching context; they're baked into prompts, not user-configurable |
| `recent_jd_job` for agent context | Simplest default — uses the job the user most recently added with a JD; avoids requiring explicit "active job" selection |
| `claude-opus-4-5` for all agents | Quality over cost for a personal tool; can split to Sonnet for cheaper agents (study/gap) in future |
| Conversations stored per-agent | Each agent maintains independent context; prevents contamination between e.g. mock interview history and resume review |
| System prompts built at call time | Ensures agents always have current data without any manual sync step |
| Hardcoded learning profile in study agents | User provided detailed learning guides; encoding them directly is more reliable than expecting the user to re-describe them |
| Buttons text color fix via `p/span/div` selectors | Streamlit renders button labels inside `<p>` tags which inherited the global `#eeedf0` text color override |
