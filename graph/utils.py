"""
Shared utilities for LangGraph nodes.

Intentionally has NO Streamlit imports — safe to call from any node.
"""

import os
import re
import json
from pathlib import Path
import anthropic


def get_anthropic_client() -> anthropic.Anthropic:
    key = os.getenv("ANTHROPIC_API_KEY", "")
    return anthropic.Anthropic(api_key=key)


def call_claude(
    messages: list,
    system: str,
    max_tokens: int = 4096,
    model: str = "claude-opus-4-5",
) -> str:
    """Simple blocking Claude call. Returns text response."""
    client = get_anthropic_client()
    try:
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=messages,
        )
        parts = [
            block.text
            for block in response.content
            if getattr(block, "type", None) == "text"
        ]
        return "\n".join(parts).strip()
    except Exception as e:
        return f"⚠️ Error: {e}"


def parse_json_response(raw: str) -> dict:
    """Extract and parse the first JSON object from a raw LLM response."""
    raw = raw.strip()
    # Strip markdown fences if present
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
    return {}


# ── Database helpers (no Streamlit dependency) ─────────────────────────────
DB_PATH = Path(__file__).parent.parent / "careeros.db"


def db_get_projects() -> list[dict]:
    """Load all projects from the SQLite project library."""
    import sqlite3
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM projects ORDER BY created_at DESC")
        rows = cur.fetchall()
        conn.close()
        result = []
        for row in rows:
            d = dict(row)
            for field in ("technologies", "metrics"):
                if isinstance(d.get(field), str):
                    try:
                        d[field] = json.loads(d[field])
                    except (json.JSONDecodeError, TypeError):
                        d[field] = []
            result.append(d)
        return result
    except Exception:
        return []


def build_project_context(projects: list[dict]) -> str:
    """Format a list of project dicts into the context block used in prompts."""
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
        if proj.get("technologies"):
            lines.append(f"  Technologies : {', '.join(proj['technologies'])}")
        if proj.get("metrics"):
            lines.append(f"  Metrics      : {' | '.join(proj['metrics'])}")
        if proj.get("contributions"):
            lines.append(f"  Contributions: {proj['contributions']}")
        if proj.get("challenges"):
            lines.append(f"  Challenges   : {proj['challenges']}")
        if proj.get("summary"):
            lines.append(f"  Summary      : {proj['summary']}")
        lines.append("")
    return "\n".join(lines)
