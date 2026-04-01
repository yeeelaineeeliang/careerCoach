"""
ProjectMatcherNode — keyword-based project ranking against a JD.

Scores each project in the Project Library by relevance to a given job
description using token overlap. Returns the top-N most relevant projects,
replacing the "inject all projects" approach with targeted retrieval.

No embeddings required — fast, deterministic, no extra dependencies.
"""

import re
from .utils import build_project_context

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


def score_project(proj: dict, jd_tokens: set[str]) -> float:
    """
    Score a project's relevance to a JD.

    Scoring:
    - 2 pts per shared token that is a known tech keyword
    - 1 pt per shared ordinary token (min 4 chars to skip noise)
    - Normalised by max(project token count, 1) to avoid length bias
    """
    proj_tokens = _tokenize(_project_text(proj))
    shared = proj_tokens & jd_tokens

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


def build_matched_project_ctx(jd: str, projects: list[dict], top_n: int = 3) -> str:
    """
    Convenience function: match projects against JD and return formatted context.
    Falls back to all projects if none score positively.
    """
    matched = match_projects(jd, projects, top_n=top_n)
    if not matched:
        return build_project_context(projects)
    return build_project_context(matched)
