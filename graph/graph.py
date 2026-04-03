"""
CareerOS LangGraph StateGraph assembly.

Graph topology:
  orchestrator → (conditional routing)
    → "direct"        → END  (coach answered inline)
    → "skills_gap"    → gap + study (parallel) → synthesis → END
    → "execution"     → project_matcher → resume → synthesis → END
    → "interview_prep"→ interview + study (parallel) → synthesis → END
    → "strategy"      → synthesizer → END
    → "outreach"      → outreach → END

The SqliteSaver checkpointer persists cross-agent state across sessions,
adding a 'checkpoints' table to the existing careeros.db.
"""

import sqlite3
from pathlib import Path
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver

from .state import CareerOSState
from .nodes import (
    orchestrator_node,
    project_matcher_node,
    gap_node,
    resume_node,
    interview_node,
    study_node,
    outreach_node,
    synthesizer_node,
    synthesis_node,
    route_after_diagnosis,
)

DB_PATH = str(Path(__file__).parent.parent / "careeros.db")

_graph_instance = None


def build_graph():
    """Build and compile the CareerOS StateGraph with SqliteSaver checkpointer."""
    workflow = StateGraph(CareerOSState)

    # ── Register nodes ──────────────────────────────────────────────────
    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("project_matcher", project_matcher_node)
    workflow.add_node("gap", gap_node)
    workflow.add_node("resume", resume_node)
    workflow.add_node("interview", interview_node)
    workflow.add_node("study", study_node)
    workflow.add_node("outreach", outreach_node)
    workflow.add_node("synthesizer", synthesizer_node)
    workflow.add_node("synthesis", synthesis_node)

    # ── Entry point ─────────────────────────────────────────────────────
    workflow.set_entry_point("orchestrator")

    # ── Conditional routing from orchestrator ───────────────────────────
    workflow.add_conditional_edges(
        "orchestrator",
        route_after_diagnosis,
        {
            "__end__": END,          # "direct" path — already answered
            "gap": "gap",
            "study": "study",
            "project_matcher": "project_matcher",
            "interview": "interview",
            "synthesizer": "synthesizer",
            "outreach": "outreach",
            "synthesis": "synthesis",
        },
    )

    # ── project_matcher feeds resume ────────────────────────────────────
    workflow.add_edge("project_matcher", "resume")

    # ── interview feeds study (sequential — study needs weak_areas) ────
    workflow.add_edge("interview", "study")

    # ── Sub-agent nodes feed synthesis ──────────────────────────────────
    for node_name in ("gap", "resume", "study"):
        workflow.add_edge(node_name, "synthesis")

    # ── Terminal nodes go to END ─────────────────────────────────────────
    workflow.add_edge("synthesizer", END)
    workflow.add_edge("outreach", END)
    workflow.add_edge("synthesis", END)

    # ── Compile with SqliteSaver checkpointer ────────────────────────────
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    checkpointer = SqliteSaver(conn)
    return workflow.compile(checkpointer=checkpointer)


def get_graph():
    """Return (and cache) the compiled graph singleton."""
    global _graph_instance
    if _graph_instance is None:
        _graph_instance = build_graph()
    return _graph_instance


def invoke_coach_graph(
    api_messages: list,
    profile: dict,
    jobs: list,
    project_ctx: str,
    calendar_connected: bool,
    resume_conversations: dict,
    career_state: dict,
    thread_id: str = "careeros_coach",
) -> tuple[str, dict, str]:
    """
    Invoke the coach graph and return (response_text, updated_career_state).

    `career_state` is a dict with keys:
      weak_areas, gap_findings, matched_projects (persisted in st.session_state)

    Returns:
      response_text  — the last assistant message to display
      updated_state  — updated career_state dict (caller saves to session_state)
    """
    graph = get_graph()

    last_user = next(
        (m["content"] for m in reversed(api_messages) if m.get("role") == "user"), ""
    )

    input_state: CareerOSState = {
        "user_message": last_user,
        "profile": profile,
        "jobs": jobs,
        "projects": [],         # lazy-loaded inside project_matcher_node if needed
        "project_ctx": project_ctx,
        "calendar_connected": calendar_connected,
        "resume_conversations": resume_conversations,
        "active_job_id": career_state.get("active_job_id"),
        "gap_findings": career_state.get("gap_findings", ""),
        "weak_areas": career_state.get("weak_areas", []),
        "resume_suggestions": "",
        "matched_projects": career_state.get("matched_projects", []),
        "study_plan": "",
        "coach_diagnosis": "",
        "messages": api_messages[-10:] if len(api_messages) > 10 else api_messages,
    }

    config = {"configurable": {"thread_id": thread_id}}
    result = graph.invoke(input_state, config=config)

    # Extract the last assistant message
    response_text = ""
    for msg in reversed(result.get("messages", [])):
        if isinstance(msg, dict) and msg.get("role") == "assistant":
            response_text = msg["content"]
            break
        elif hasattr(msg, "content"):
            response_text = msg.content
            break

    # Build updated career_state with any new findings
    updated_career_state = dict(career_state)
    if result.get("weak_areas"):
        updated_career_state["weak_areas"] = result["weak_areas"]
    if result.get("gap_findings"):
        updated_career_state["gap_findings"] = result["gap_findings"]
    if result.get("matched_projects"):
        updated_career_state["matched_projects"] = result["matched_projects"]
    if result.get("active_job_id") is not None:
        updated_career_state["active_job_id"] = result["active_job_id"]

    diagnosis = result.get("coach_diagnosis", "direct")
    return response_text or "⚠️ No response generated.", updated_career_state, diagnosis
