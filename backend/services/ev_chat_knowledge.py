from __future__ import annotations

import re
from pathlib import Path

from pydantic import BaseModel

from .ev_policy import get_state_policy_note


class KnowledgeArticle(BaseModel):
    slug: str
    title: str
    content: str
    path: str


ARTICLE_DIR = Path(__file__).resolve().parent.parent / "data" / "articles"


def load_knowledge_articles() -> list[KnowledgeArticle]:
    articles: list[KnowledgeArticle] = []
    if not ARTICLE_DIR.exists():
        return articles

    for path in sorted(ARTICLE_DIR.glob("*.md")):
        content = path.read_text(encoding="utf-8")
        title = next((line.lstrip("# ").strip() for line in content.splitlines() if line.startswith("# ")), path.stem)
        articles.append(
            KnowledgeArticle(
                slug=path.stem,
                title=title,
                content=content,
                path=str(path),
            )
        )
    return articles


def is_location_query(query: str) -> bool:
    q = (query or "").lower()
    return any(
        token in q
        for token in [
            "charging station",
            "charging stations",
            "charging point",
            "charging points",
            "charger near",
            "nearby charger",
            "fast charging points",
        ]
    )


def is_policy_query(query: str) -> bool:
    q = (query or "").lower()
    return any(token in q for token in ["subsidy", "incentive", "fame", "pm e-drive", "pm e drive"])


def is_limitations_query(query: str) -> bool:
    q = (query or "").lower()
    return "limitation" in q or "what can you not" in q or "what are your boundaries" in q


def is_identity_query(query: str) -> bool:
    q = re.sub(r"\s+", " ", (query or "").lower()).strip()
    return q in {"who are you", "who r you", "who are u", "what are you"} or "who are you?" in q or "who are u?" in q


def is_capabilities_query(query: str) -> bool:
    q = re.sub(r"\s+", " ", (query or "").lower()).strip()
    return (
        q in {"what can you do", "what do you do", "help me", "what all can you do"}
        or "what can you do?" in q
        or "how can you help" in q
    )


def is_ev_concept_query(query: str) -> bool:
    q = (query or "").lower()
    concept_tokens = [
        "tco",
        "total cost of ownership",
        "charging",
        "battery",
        "regen",
        "regenerative",
        "lfp",
        "nmc",
        "running cost",
        "petrol",
        "rain",
        "thermal management",
        "c-rating",
        "c rate",
        "pmsm",
        "bldc",
        "v2l",
        "v2v",
        "cell balancing",
        "bms",
    ]
    return any(token in q for token in concept_tokens) or q.startswith("what is ") or q.startswith("explain ")


def retrieve_knowledge_articles(query: str, articles: list[KnowledgeArticle], top_k: int = 2) -> list[KnowledgeArticle]:
    q_tokens = set(re.findall(r"[a-z0-9]+", (query or "").lower()))
    scored: list[tuple[float, KnowledgeArticle]] = []

    for article in articles:
        title_tokens = set(re.findall(r"[a-z0-9]+", article.title.lower()))
        content_tokens = set(re.findall(r"[a-z0-9]+", article.content.lower()))
        title_overlap = len(q_tokens.intersection(title_tokens))
        content_overlap = len(q_tokens.intersection(content_tokens))
        score = (title_overlap * 2.5) + (content_overlap * 0.4)
        if "tco" in q_tokens and ("ownership" in title_tokens or "ownership" in content_tokens):
            score += 5
        if ("tco" in q_tokens or "ownership" in q_tokens) and "total_cost_of_ownership" in article.slug:
            score += 8
        if "subsidy" in q_tokens and "subsidies" in title_tokens:
            score += 4
        if score > 0:
            scored.append((score, article))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [article for _, article in scored[:top_k]]


def _clean_markdown_line(line: str) -> str:
    cleaned = re.sub(r"^\s*[#>\-*]+\s*", "", line).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned


def extract_supporting_lines(article: KnowledgeArticle, query: str, limit: int = 4) -> list[str]:
    q_tokens = set(re.findall(r"[a-z0-9]+", (query or "").lower()))
    scored: list[tuple[float, str]] = []

    for index, raw_line in enumerate(article.content.splitlines()):
        line = _clean_markdown_line(raw_line)
        if len(line) < 24:
            continue
        if line == article.title:
            continue
        if raw_line.startswith("#") and ":" not in line:
            continue
        line_tokens = set(re.findall(r"[a-z0-9]+", line.lower()))
        overlap = len(q_tokens.intersection(line_tokens))
        if overlap == 0 and index > 24:
            continue
        score = overlap + max(0, 2.0 - (index * 0.04))
        scored.append((score, line))

    scored.sort(key=lambda item: item[0], reverse=True)
    unique_lines: list[str] = []
    seen: set[str] = set()
    for _, line in scored:
        if line in seen:
            continue
        seen.add(line)
        unique_lines.append(line)
        if len(unique_lines) >= limit:
            break
    return unique_lines


def build_policy_answer(query: str, state: str | None) -> str:
    state_note = get_state_policy_note(state)
    q = (query or "").lower()

    if state_note:
        return (
            f"{state_note}\n\n"
            f"- Location used: {state}.\n"
            "- Subsidies are policy-sensitive and can change the affordability picture.\n\n"
            "Use this as policy context, but verify dealer-final subsidy and eligibility before purchase.\n\n"
            "Tell me your budget and segment and I can shortlist EVs with price, charging, and range trade-offs."
        )

    if "scooter" in q or "2w" in q or "two wheeler" in q:
        return (
            "For electric scooters, subsidy is policy-sensitive rather than one fixed amount for every model.\n\n"
            "- Vehicle type used: 2W/scooter.\n"
            "- Final benefit depends on state, model eligibility, and current policy snapshot.\n\n"
            "Compare segment, battery size, and your state before trusting a final rupee number.\n\n"
            "Which state and budget should I use?"
        )

    return (
        "Subsidy answers are policy-sensitive, so I keep them conservative.\n\n"
        "- Location and vehicle segment are not fully specified.\n"
        "- Final subsidy can depend on state, segment, model eligibility, and dealer quote.\n\n"
        "Tell me your state and vehicle segment if you want a grounded shortlist.\n\n"
        "Which state and vehicle type should I use?"
    )


def build_limitations_answer() -> str:
    return (
        "I stay grounded in the current EV dataset and EViq knowledge articles.\n\n"
        "That means I can compare listed specs, explain EV concepts, and build shortlists from the available data, but I should not guess missing specs, live prices, live subsidies, dealer stock, or route-specific charging availability.\n\n"
        "If you want, I can still help by showing the closest grounded shortlist and clearly marking the caveats."
    )


def build_identity_answer() -> str:
    return (
        "I’m EViq Expert, your EV assistant for this app.\n\n"
        "I help with Indian EV recommendations, comparisons, charging, TCO, subsidies, and model-specific questions using the current dataset and EV knowledge base.\n\n"
        "If a detail is missing, I’ll say that clearly instead of making it up."
    )


def build_capabilities_answer() -> str:
    return (
        "I can help with both EV advice and dataset-based lookups.\n\n"
        "For example, I can recommend EVs by budget or use case, compare two models, explain charging or battery topics, answer TCO questions, and summarize what is available in the current EV dataset.\n\n"
        "If you want, ask me something like `best EV car under 15 lakh`, `compare Nexon EV vs MG ZS EV`, or `explain TCO`."
    )
