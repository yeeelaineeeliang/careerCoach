"""
Shared state schema for the CareerOS LangGraph multi-agent system.

CareerOSState flows through the graph, accumulating findings from each
agent node so downstream nodes can read and build on prior results.
"""

import operator
from typing import Annotated
from typing_extensions import TypedDict


class CareerOSState(TypedDict):
    # ── Input / context (loaded at graph entry) ───────────────────────────
    user_message: str
    profile: dict                    # Full profile dict (name, resume, goals, etc.)
    jobs: list                       # All tracked jobs
    projects: list                   # All projects from Project Library
    project_ctx: str                 # Pre-formatted project context string
    calendar_connected: bool         # Whether Google Calendar is connected
    resume_conversations: dict       # {job_id_str: [{role, content}...]} for synthesizer
    active_job_id: int | None        # The job the user is currently working on

    # ── Agent findings (written by nodes, read by downstream nodes) ────────
    gap_findings: str                # GapNode output — fit score + critical gaps
    weak_areas: list[str]            # InterviewNode → StudyNode
    resume_suggestions: str          # ResumeNode output
    matched_projects: list[dict]     # ProjectMatcherNode → ResumeNode
    study_plan: str                  # StudyNode output

    # ── Orchestrator metadata ──────────────────────────────────────────────
    coach_diagnosis: str             # "direct" | "skills_gap" | "execution" |
                                     # "interview_prep" | "strategy" | "outreach"

    # ── Accumulated messages (all agent responses append here) ────────────
    messages: Annotated[list, operator.add]
