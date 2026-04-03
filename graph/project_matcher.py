"""
ProjectMatcherNode — keyword-based project ranking against a JD.

Scores each project in the Project Library by relevance to a given job
description using token overlap. Returns the top-N most relevant projects,
replacing the "inject all projects" approach with targeted retrieval.

No embeddings required — fast, deterministic, no extra dependencies.
"""

import json
import re
from .utils import build_project_context, call_claude

# Technology keywords that carry strong signal if they appear in both JD and project
_TECH_SIGNAL_WORDS = {
    # ML / AI
    "pytorch", "tensorflow", "keras", "sklearn", "xgboost", "lightgbm",
    "transformers", "bert", "gpt", "llm", "rag", "faiss", "embedding",
    "fine-tuning", "finetuning", "mlops", "mlflow", "wandb", "huggingface",
    # Data
    "pandas", "numpy", "sql", "spark", "airflow", "dbt", "bigquery",
    "postgres", "mysql", "mongodb", "redis",
    # Systems / SWE
    "fastapi", "flask", "django", "react", "typescript", "node",
    "docker", "kubernetes", "aws", "gcp", "azure", "lambda", "terraform",
    "ci/cd", "github actions", "api", "rest", "graphql",
    # Languages
    "python", "java", "golang", "go", "rust", "scala", "c++", "cpp",
    "javascript", "typescript",
}


def _tokenize(text: str) -> set[str]:
    """Lowercase, strip punctuation, return set of word tokens."""
    text = text.lower()
    # Keep hyphens within words (e.g. "fine-tuning")
    tokens = re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*", text)
    return set(tokens)


def _project_text(proj: dict) -> str:
    """Flatten all text fields of a project into one string."""
    parts = [
        proj.get("title", ""),
        proj.get("summary", ""),
        proj.get("contributions", ""),
        proj.get("challenges", ""),
        " ".join(proj.get("technologies", [])),
        " ".join(proj.get("metrics", [])),
    ]
    return " ".join(p for p in parts if p)


# Domain clusters — if a JD mentions ANY word in a cluster, all words in that
# cluster become "virtual JD tokens" for matching.  This lets a distributed-
# systems project match a generic SWE JD that never says "raft" or "consensus".
_DOMAIN_CLUSTERS = {
    frozenset({"distributed", "consensus", "replication", "fault-tolerance", "raft", "paxos", "message-queue", "queue", "kafka", "grpc"}):
        frozenset({"backend", "infrastructure", "systems", "scalable", "microservice", "microservices", "sre", "reliability"}),
    frozenset({"ml", "machine-learning", "model", "training", "inference", "fine-tuning", "finetuning", "embeddings", "rag", "llm", "transformers", "nlp"}):
        frozenset({"ai", "data-science", "deep-learning", "neural", "prediction", "classifier", "regression"}),
    frozenset({"ci/cd", "docker", "kubernetes", "terraform", "jenkins", "helm", "devops", "pipeline"}):
        frozenset({"deploy", "deployment", "cloud", "infrastructure", "automation", "containerized"}),
    frozenset({"react", "typescript", "frontend", "nextjs", "next-js", "tailwind", "css", "html"}):
        frozenset({"ui", "web", "full-stack", "fullstack", "component", "responsive"}),
    frozenset({"ios", "swift", "swiftui", "mobile", "android", "kotlin", "flutter"}):
        frozenset({"app", "mobile", "native"}),
}


def _expand_jd_tokens(jd_tokens: set[str]) -> set[str]:
    """Expand JD tokens with domain cluster words when there's a domain match."""
    expanded = set(jd_tokens)
    for cluster_a, cluster_b in _DOMAIN_CLUSTERS.items():
        if jd_tokens & cluster_a or jd_tokens & cluster_b:
            expanded |= cluster_a | cluster_b
    return expanded


def score_project(proj: dict, jd_tokens: set[str]) -> float:
    """
    Score a project's relevance to a JD.

    Scoring:
    - 2 pts per shared token that is a known tech keyword
    - 1 pt per shared ordinary token (min 4 chars to skip noise)
    - Domain cluster expansion: if JD mentions "backend", projects with
      "distributed", "consensus", "raft" etc. also match
    - Normalised by max(project token count, 1) to avoid length bias
    """
    expanded = _expand_jd_tokens(jd_tokens)
    proj_tokens = _tokenize(_project_text(proj))
    shared = proj_tokens & expanded

    score = 0.0
    for token in shared:
        if token in _TECH_SIGNAL_WORDS:
            score += 2.0
        elif len(token) >= 4:
            score += 1.0

    # Normalise slightly so short projects aren't over-penalised
    norm = max(len(proj_tokens), 1)
    return score / (norm ** 0.3)


def match_projects(jd: str, projects: list[dict], top_n: int = 3) -> list[dict]:
    """
    Rank projects by relevance to `jd` and return the top `top_n`.

    Each returned project dict has an extra "_relevance_score" key.
    Returns all projects if len(projects) <= top_n (no filtering needed).
    """
    if not projects or len(projects) <= top_n:
        return projects

    jd_tokens = _tokenize(jd)
    scored = [(score_project(p, jd_tokens), p) for p in projects]
    scored.sort(key=lambda x: x[0], reverse=True)

    result = []
    for score, proj in scored[:top_n]:
        p = dict(proj)
        p["_relevance_score"] = round(score, 3)
        result.append(p)
    return result


def build_matched_project_ctx(jd: str, projects: list[dict], top_n: int = 5) -> str:
    """
    Convenience function: match projects against JD and return formatted context.
    Falls back to all projects if none score positively.
    """
    matched = match_projects(jd, projects, top_n=top_n)
    if not matched:
        return build_project_context(projects)
    return build_project_context(matched)


# ── LLM-based semantic ranking (for large libraries) ─────────────────────────

def _parse_index_list(raw: str) -> list[int] | None:
    """Extract a JSON array of integers from an LLM response."""
    raw = raw.strip().strip("`").strip()
    match = re.search(r"\[[\d,\s]+\]", raw)
    if match:
        try:
            result = json.loads(match.group())
            if isinstance(result, list) and all(isinstance(x, int) for x in result):
                return result
        except json.JSONDecodeError:
            pass
    return None


def llm_rank_projects(
    jd: str, company: str, projects: list[dict], top_n: int = 5
) -> list[dict]:
    """
    Use Haiku to semantically rank projects against a JD.

    Considers technology overlap, domain relevance, and company industry —
    unlike the keyword matcher which only sees exact token overlap.
    Falls back to keyword matching if the LLM call fails.
    """
    summaries = []
    for i, p in enumerate(projects):
        title = p.get("title", "Untitled")
        summary = (p.get("summary") or "")[:200]
        techs = ", ".join(p.get("technologies", [])[:5])
        summaries.append(f"[{i}] {title} | {techs} | {summary}")

    project_list = "\n".join(summaries)

    prompt = (
        f"Rank these projects by relevance to the job description below.\n"
        f"Consider: technology overlap, domain relevance, company industry/mission, "
        f"and transferable skills.\n"
        f"The company is: {company}\n\n"
        f"JD (excerpt):\n{jd[:1500]}\n\n"
        f"Projects:\n{project_list}\n\n"
        f"Return ONLY a JSON array of the top {top_n} project indices, most relevant first.\n"
        f"Example: [3, 0, 7, 1, 5]"
    )

    raw = call_claude(
        messages=[{"role": "user", "content": prompt}],
        system="You rank project relevance. Return only a JSON array of integer indices.",
        max_tokens=100,
        model="claude-haiku-4-5-20251001",
    )

    indices = _parse_index_list(raw)
    if indices:
        ranked = [
            projects[i] for i in indices
            if isinstance(i, int) and 0 <= i < len(projects)
        ][:top_n]
        if ranked:
            return ranked

    # Fallback: keyword matcher with higher top_n
    return match_projects(jd, projects, top_n=top_n)
