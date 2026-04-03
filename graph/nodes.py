"""
LangGraph node functions for the CareerOS multi-agent system.

Each node receives CareerOSState, calls the relevant agent, writes its
findings back to state, and returns a partial state update dict.

No Streamlit imports here — all data comes in via state.
"""

import re
import sys
from pathlib import Path

# Make the parent directory importable so `prompts` can be found
sys.path.insert(0, str(Path(__file__).parent.parent))

from .state import CareerOSState
from .utils import call_claude, parse_json_response, db_get_projects, build_project_context
from .project_matcher import match_projects, build_matched_project_ctx, llm_rank_projects
from prompts import build_system_prompt

# ── Diagnosis classification ────────────────────────────────────────────────

_DIAGNOSIS_SYSTEM = """You classify a career coaching message into exactly one intent category.
Return ONLY a valid JSON object — no markdown, no prose."""

_DIAGNOSIS_PROMPT = """Classify the user's primary intent and return JSON:

{{
  "diagnosis": "<category>",
  "active_job_id": <integer or null>,
  "reasoning": "<one line>"
}}

Categories:
- "direct": simple question, status check, casual chat, pipeline overview — answer directly without sub-agents
- "skills_gap": fit assessment, "should I apply", what gaps exist, competitiveness for a role
- "execution": resume tailoring, bullet rewrites, JD keyword alignment
- "interview_prep": mock interview, practice questions, interview prep
- "strategy": multi-company planning, resume synthesis, cross-application patterns
- "outreach": LinkedIn message, cold DM, referral request, follow-up draft

User message: {message}

Active jobs (for extracting active_job_id):
{jobs_summary}
"""


def orchestrator_node(state: CareerOSState) -> dict:
    """
    Entry node: classify the user's intent.

    For "direct" diagnosis → generates a full coach response immediately.
    For all other diagnoses → sets coach_diagnosis for conditional routing.
    """
    messages = state.get("messages", [])
    if not messages:
        return {"coach_diagnosis": "direct", "messages": []}

    last_user = next(
        (m["content"] for m in reversed(messages) if m.get("role") == "user"), ""
    )

    # ── Keyword fast-path: skip Haiku call for obvious intents ──────────
    _lower = last_user.lower()
    _keyword_diagnosis = None
    if any(kw in _lower for kw in ("mock interview", "practice question", "interview prep", "behavioral question", "technical question")):
        _keyword_diagnosis = "interview_prep"
    elif any(kw in _lower for kw in ("rewrite", "resume", "bullet", "tailor")):
        _keyword_diagnosis = "execution"
    elif any(kw in _lower for kw in ("linkedin", "cold dm", "outreach", "referral request", "follow-up", "cold email")):
        _keyword_diagnosis = "outreach"
    elif any(kw in _lower for kw in ("gap", "fit score", "should i apply", "how competitive", "what gaps")):
        _keyword_diagnosis = "skills_gap"

    if _keyword_diagnosis:
        diagnosis = _keyword_diagnosis
        active_job_id = None
        # Try to extract job ID from message (e.g., "for job 3")
        import re as _re
        _id_match = _re.search(r'(?:job|id)\s*#?\s*(\d+)', _lower)
        if _id_match:
            active_job_id = int(_id_match.group(1))
        elif len(state.get("jobs", [])) == 1:
            active_job_id = state["jobs"][0]["id"]
    else:
        # Ambiguous — fall back to Haiku classification
        jobs_summary = "\n".join(
            f"[ID:{j['id']}] {j['company']} | {j['role']} | {j['status']}"
            for j in state.get("jobs", [])
        ) or "No jobs tracked."

        raw = call_claude(
            messages=[{"role": "user", "content": _DIAGNOSIS_PROMPT.format(
                message=last_user[:800],
                jobs_summary=jobs_summary,
            )}],
            system=_DIAGNOSIS_SYSTEM,
            max_tokens=256,
            model="claude-haiku-4-5-20251001",
        )
        parsed = parse_json_response(raw)
        diagnosis = parsed.get("diagnosis", "direct")
        active_job_id = parsed.get("active_job_id")

    # Validate diagnosis value
    valid = {"direct", "skills_gap", "execution", "interview_prep", "strategy", "outreach"}
    if diagnosis not in valid:
        diagnosis = "direct"

    updates: dict = {"coach_diagnosis": diagnosis}
    if active_job_id is not None:
        updates["active_job_id"] = active_job_id

    if diagnosis == "direct":
        # Answer immediately — no sub-agents needed
        system = build_system_prompt(
            "coach",
            profile=state["profile"],
            jobs=state["jobs"],
            project_ctx=state.get("project_ctx", ""),
            calendar_connected=state.get("calendar_connected", False),
            resume_conversations=state.get("resume_conversations", {}),
            weak_areas=state.get("weak_areas", []),
            gap_findings=state.get("gap_findings", ""),
        )
        response = call_claude(messages, system)
        updates["messages"] = [{"role": "assistant", "content": response}]

    return updates


# ── Sub-agent nodes ─────────────────────────────────────────────────────────

def _get_job(state: CareerOSState) -> dict | None:
    """Look up the active job from state."""
    job_id = state.get("active_job_id")
    if job_id is None:
        return None
    return next((j for j in state.get("jobs", []) if j["id"] == job_id), None)


def project_matcher_node(state: CareerOSState) -> dict:
    """
    Run before ResumeNode: rank Project Library items against the active JD.
    Writes matched_projects and an updated project_ctx to state.

    For small libraries (<=8 projects), passes all projects through so the
    Resume Reviewer LLM can use semantic/domain reasoning to pick the best ones.
    For larger libraries, uses Haiku-based semantic ranking to select top 5.
    """
    PASS_ALL_THRESHOLD = 8

    job = _get_job(state)
    if not job or not job.get("jd"):
        return {}

    projects = state.get("projects") or db_get_projects()
    if not projects:
        return {}

    if len(projects) <= PASS_ALL_THRESHOLD:
        matched = projects
    else:
        matched = llm_rank_projects(
            job["jd"], job.get("company", ""), projects, top_n=5
        )

    matched_ctx = build_project_context(matched)

    return {
        "matched_projects": matched,
        "project_ctx": matched_ctx,
    }


def gap_node(state: CareerOSState) -> dict:
    """Run a gap analysis for the active job."""
    job = _get_job(state)
    system = build_system_prompt(
        "gap",
        profile=state["profile"],
        jobs=state["jobs"],
        job=job,
        project_ctx=state.get("project_ctx", ""),
    )
    task = (
        f"Run a full gap analysis for {job['company']} — {job['role']}."
        if job
        else "Run a gap analysis across my active applications."
    )
    response = call_claude([{"role": "user", "content": task}], system, max_tokens=1200)
    return {
        "gap_findings": response,
        "messages": [{"role": "assistant", "content": f"**Gap Analysis**\n\n{response}"}],
    }


def resume_node(state: CareerOSState) -> dict:
    """Rewrite and optimise resume bullets for the active job."""
    job = _get_job(state)

    # Return cached result if resume was already generated for this job + JD
    cached = state.get("resume_cache", {})
    job_id = str(job["id"]) if job else ""
    jd_hash = str(hash(job.get("jd", ""))) if job else ""
    cache_key = f"{job_id}:{jd_hash}"
    if cache_key in cached:
        prev = cached[cache_key]
        return {
            "resume_suggestions": prev,
            "messages": [{"role": "assistant", "content": f"**Resume Review** (cached — same JD)\n\n{prev}"}],
        }

    # Use matched_projects context if available (set by project_matcher_node)
    project_ctx = state.get("project_ctx", "")
    system = build_system_prompt(
        "resume",
        profile=state["profile"],
        jobs=state["jobs"],
        job=job,
        project_ctx=project_ctx,
    )
    task = (
        f"Review and rewrite the resume for {job['company']} — {job['role']}."
        if job
        else "Review and rewrite the resume for the most recent active role."
    )
    response = call_claude([{"role": "user", "content": task}], system, max_tokens=2000)

    # Cache the result
    cached[cache_key] = response
    return {
        "resume_suggestions": response,
        "resume_cache": cached,
        "messages": [{"role": "assistant", "content": f"**Resume Review**\n\n{response}"}],
    }


def interview_node(state: CareerOSState) -> dict:
    """Run interview prep for the active job and extract weak areas."""
    job = _get_job(state)
    system = build_system_prompt(
        "interview",
        profile=state["profile"],
        jobs=state["jobs"],
        job=job,
    )
    task = (
        f"Run interview prep for {job['company']} — {job['role']}. Start with the most likely question types."
        if job
        else "Run interview prep for the most recent active role."
    )
    response = call_claude([{"role": "user", "content": task}], system, max_tokens=2000)

    weak_areas = extract_weak_areas(response)

    return {
        "messages": [{"role": "assistant", "content": f"**Interview Prep**\n\n{response}"}],
        **({"weak_areas": weak_areas} if weak_areas else {}),
    }


def study_node(state: CareerOSState) -> dict:
    """Build a study plan, prioritising confirmed weak areas from interviews."""
    job = _get_job(state)
    system = build_system_prompt(
        "study",
        profile=state["profile"],
        jobs=state["jobs"],
        job=job,
        weak_areas=state.get("weak_areas", []),
    )
    task = (
        f"Build a study plan for {job['company']} — {job['role']}."
        if job
        else "Build a study plan across all my active applications."
    )
    response = call_claude([{"role": "user", "content": task}], system, max_tokens=1200)
    return {
        "study_plan": response,
        "messages": [{"role": "assistant", "content": f"**Study Plan**\n\n{response}"}],
    }


def outreach_node(state: CareerOSState) -> dict:
    """Draft outreach messages."""
    job = _get_job(state)
    system = build_system_prompt(
        "outreach",
        profile=state["profile"],
        jobs=state["jobs"],
    )
    last_user = next(
        (m["content"] for m in reversed(state.get("messages", [])) if m.get("role") == "user"),
        "Draft an outreach message.",
    )
    response = call_claude([{"role": "user", "content": last_user}], system, max_tokens=1000)
    return {
        "messages": [{"role": "assistant", "content": response}],
    }


def synthesizer_node(state: CareerOSState) -> dict:
    """Run the resume synthesizer across all tracked JDs."""
    system = build_system_prompt(
        "synthesizer",
        profile=state["profile"],
        jobs=state["jobs"],
        resume_conversations=state.get("resume_conversations", {}),
        project_ctx=state.get("project_ctx", ""),
    )
    last_user = next(
        (m["content"] for m in reversed(state.get("messages", [])) if m.get("role") == "user"),
        "Analyze patterns across all my JDs and produce optimized resume versions.",
    )
    response = call_claude([{"role": "user", "content": last_user}], system, max_tokens=2400)
    return {
        "messages": [{"role": "assistant", "content": response}],
    }


def synthesis_node(state: CareerOSState) -> dict:
    """
    Final coach synthesis: integrates sub-agent findings into a coherent response.

    Runs the full coach system prompt + sub-agent findings, then produces the
    final user-facing response.
    """
    # Build enhanced coach system prompt with all findings injected
    system = build_system_prompt(
        "coach",
        profile=state["profile"],
        jobs=state["jobs"],
        project_ctx=state.get("project_ctx", ""),
        calendar_connected=state.get("calendar_connected", False),
        resume_conversations=state.get("resume_conversations", {}),
        weak_areas=state.get("weak_areas", []),
        gap_findings=state.get("gap_findings", ""),
    )

    # Append all sub-agent outputs as context for the synthesis
    findings_blocks = []
    if state.get("gap_findings"):
        findings_blocks.append(f"=== GAP ANALYSIS RESULT ===\n{state['gap_findings']}")
    if state.get("resume_suggestions"):
        findings_blocks.append(f"=== RESUME REVIEW RESULT ===\n{state['resume_suggestions']}")
    if state.get("study_plan"):
        findings_blocks.append(f"=== STUDY PLAN RESULT ===\n{state['study_plan']}")

    # Skip the extra LLM call if only one sub-agent produced output —
    # just return that output directly to save tokens.
    if len(findings_blocks) <= 1 and findings_blocks:
        return {}  # sub-agent message already in state, no need to re-synthesize

    if findings_blocks:
        findings_text = "\n\n".join(findings_blocks)
        system += (
            "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "SUB-AGENT FINDINGS (synthesize these into your response):\n\n"
            + findings_text
            + "\n\nSynthesize the above findings into a single cohesive response. "
            "Lead with the most actionable insight. Do NOT paste raw output verbatim."
        )

    # Use the original conversation history for synthesis
    conv_messages = [
        m for m in state.get("messages", [])
        if isinstance(m, dict) and m.get("role") in ("user", "assistant")
        # Exclude the sub-agent result messages we just injected into system
        and not any(
            m.get("content", "").startswith(prefix)
            for prefix in ("**Gap Analysis**", "**Resume Review**", "**Study Plan**", "**Interview Prep**")
        )
    ]

    if not conv_messages:
        return {}

    response = call_claude(conv_messages, system, max_tokens=1600)
    return {
        "messages": [{"role": "assistant", "content": response}],
    }


# ── Routing ─────────────────────────────────────────────────────────────────

def route_after_diagnosis(state: CareerOSState) -> list[str]:
    """
    Conditional routing after OrchestratorNode.

    Returns list of next node names. LangGraph runs them in parallel when
    multiple names are returned.
    """
    d = state.get("coach_diagnosis", "direct")

    if d == "direct":
        # Already answered in orchestrator_node — go straight to END
        return ["__end__"]
    elif d == "skills_gap":
        return ["gap", "study"]                  # parallel
    elif d == "execution":
        return ["project_matcher"]               # project_matcher → resume (sequential)
    elif d == "interview_prep":
        return ["interview"]                     # sequential: interview → study (needs weak_areas)
    elif d == "strategy":
        return ["synthesizer"]
    elif d == "outreach":
        return ["outreach"]
    else:
        return ["synthesis"]


# ── Cross-agent extraction helpers ──────────────────────────────────────────

_WEAK_AREA_PATTERNS = [
    # "I've noticed you tend to X"
    r"you tend to (.{5,60}?)[\.\n]",
    # "⚠️ What missed — ..."
    r"What missed[^:]*[:\-]\s*(.{5,60}?)[\.\n]",
    # "pattern: X"
    r"pattern[:\s]+(.{5,60}?)[\.\n]",
    # Explicit "weak in X" / "weakness in X"
    r"weak(?:ness)?(?:\s+in|\s+areas?)?[:\s]+(.{5,60}?)[\.\n]",
]


def extract_weak_areas(interview_response: str) -> list[str]:
    """
    Parse an interview coach response to extract confirmed weak areas.
    Returns a deduplicated list of up to 5 short area strings.
    """
    areas: list[str] = []
    seen: set[str] = set()

    for pattern in _WEAK_AREA_PATTERNS:
        for match in re.finditer(pattern, interview_response, re.IGNORECASE):
            area = match.group(1).strip()
            area = re.sub(r"\s+", " ", area)
            # Skip very short or very long matches
            if len(area) < 5 or len(area) > 80:
                continue
            key = area.lower()
            if key not in seen:
                seen.add(key)
                areas.append(area)
            if len(areas) >= 5:
                break
        if len(areas) >= 5:
            break

    return areas
