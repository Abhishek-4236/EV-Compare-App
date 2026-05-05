from __future__ import annotations

import json
import logging
import re
from typing import Any
from urllib import error, request

from core.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert EV assistant for India.

- Answer like a real human expert: short, structured, practical, and specific.
- Help across 2W, 3W, 4W, buses, and commercial EVs.
- Do not use rigid labels like Answer, Why, Suggestion, or Optional.
- Prefer tables for comparisons and structured lists for recommendations.
- Detect the user's intent: Recommendation, Comparison, Cost (TCO), Technical, or Policy/Subsidy.
- Preserve extracted anchors when present: budget, daily usage, location, and vehicle type.
- For TCO, preserve the app rule that EV running cost is about ₹1/km and petrol is about ₹8/km when that appears in the draft.

Strict grounding rules:
- Use only the provided dataset/context and the grounded draft.
- Do not add outside facts, live market claims, or assumptions.
- If context is missing or weak, return exactly: Not enough data available.
- Preserve vehicle names, numbers, caveats, and table rows from the draft/context.
- Ask a clarification question when the request is vague."""


def _clean_text_block(text: str, max_chars: int = 420) -> str:
    cleaned = re.sub(r"```.*?```", " ", text or "", flags=re.DOTALL)
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = cleaned.strip(" \n-*")
    if len(cleaned) > max_chars:
        cleaned = cleaned[:max_chars].rsplit(" ", 1)[0].rstrip(" ,;:.-") + "..."
    return cleaned


def prepare_context_chunks(chunks: list[str], top_k: int | None = None) -> list[str]:
    limit = top_k or settings.RAG_TOP_K
    prepared: list[str] = []
    seen: set[str] = set()
    for chunk in chunks:
        cleaned = _clean_text_block(chunk)
        if len(cleaned) < 24:
            continue
        dedupe_key = cleaned.lower()
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        prepared.append(cleaned)
        if len(prepared) >= limit:
            break
    return prepared


def _format_history(history: list[dict[str, str]] | None, max_items: int = 6) -> str:
    if not history:
        return "None"
    lines: list[str] = []
    for item in history[-max_items:]:
        role = (item.get("role") or "user").strip().lower()
        content = item.get("content") or item.get("text") or ""
        cleaned = _clean_text_block(content, max_chars=220)
        if cleaned:
            lines.append(f"{role.title()}: {cleaned}")
    return "\n".join(lines) if lines else "None"


def _build_user_prompt(
    *,
    query: str,
    context_chunks: list[str],
    history: list[dict[str, str]] | None,
    general_only: bool,
    draft_answer: str,
    query_type: str | None = None,
    user_level: str | None = None,
) -> str:
    context_block = "\n".join(f"{index}. {chunk}" for index, chunk in enumerate(context_chunks, start=1)) or "None"
    grounding_note = (
        "No relevant dataset context was found. Return exactly: Not enough data available."
        if general_only or not context_chunks
        else "Use the retrieved context for every factual claim."
    )
    return (
        "You are improving a grounded EV answer so it feels natural and conversational.\n\n"
        "Your job:\n"
        "- Rewrite the draft answer in a more human, ChatGPT-like way.\n"
        "- Keep the same facts, numbers, caveats, and meaning as the draft.\n"
        "- Do not add new facts that are not already supported by the draft or retrieved context.\n"
        "- Preserve the exact vehicle names from the draft and context.\n"
        "- Never replace a compared vehicle with a different model, even if names seem similar.\n"
        "- If the draft contains a markdown table, preserve the same rows, values, and model order.\n"
        "- If the user asks for table format, keep the answer in markdown table format.\n"
        "- Do not add rigid section labels like Answer, Why, Suggestion, or Optional.\n"
        "- If you are not fully confident, stay very close to the draft instead of improvising.\n"
        "- Start with a direct answer.\n"
        "- Then explain clearly.\n"
        "- Adapt depth to the detected user level: beginner means plain language, intermediate means concise reasoning, advanced means precise trade-offs.\n"
        "- Adapt structure to the query type: conceptual uses explanation, decision uses comparison and recommendation, dataset uses direct grounded answer, short factual stays brief.\n"
        "- Use bullets only when they genuinely help readability.\n"
        "- Do not output labels like 'User question:' or overly robotic section headings.\n"
        "- If the draft says 'Not enough data available', return exactly that sentence.\n"
        "- Do not include unsupported general guidance.\n"
        f"- {grounding_note}\n\n"
        f"Detected query type: {query_type or 'dataset'}\n"
        f"Detected user level: {user_level or 'intermediate'}\n\n"
        f"User question:\n{query}\n\n"
        f"Grounded draft answer to rewrite:\n{draft_answer}\n\n"
        f"Recent chat context:\n{_format_history(history)}\n\n"
        f"Retrieved EV context (top {settings.RAG_TOP_K} chunks max):\n{context_block}"
    )


def _generate_with_hf_router_chat(model: str, messages: list[dict[str, str]]) -> str:
    if not settings.HF_API_KEY:
        raise RuntimeError("HF_API_KEY is not configured")
    payload = json.dumps(
        {
            "model": model,
            "messages": messages,
            "temperature": 0.25,
            "max_tokens": 420,
        }
    ).encode("utf-8")
    req = request.Request(
        "https://router.huggingface.co/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {settings.HF_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=settings.LLM_TIMEOUT_SECONDS) as response:
            body = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"HF router request failed: {exc.code} {detail}") from exc

    choices = body.get("choices") or []
    if not choices:
        raise RuntimeError("HF router returned no choices")
    content = ((choices[0] or {}).get("message") or {}).get("content") or ""
    return str(content).strip()


def _generate_with_groq_direct(messages: list[dict[str, str]]) -> str:
    if not settings.GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is not configured")
    payload = json.dumps(
        {
            "model": settings.GROQ_MODEL,
            "messages": messages,
            "temperature": 0.25,
            "max_tokens": 420,
        }
    ).encode("utf-8")
    req = request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {settings.GROQ_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=settings.LLM_TIMEOUT_SECONDS) as response:
            body = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Groq request failed: {exc.code} {detail}") from exc

    choices = body.get("choices") or []
    if not choices:
        raise RuntimeError("Groq returned no choices")
    content = ((choices[0] or {}).get("message") or {}).get("content") or ""
    return str(content).strip()


def generate_chat_response(
    *,
    query: str,
    context_chunks: list[str],
    draft_answer: str,
    history: list[dict[str, str]] | None = None,
    general_only: bool = False,
    query_type: str | None = None,
    user_level: str | None = None,
) -> tuple[str | None, str | None]:
    if general_only or not context_chunks:
        return None, None

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": _build_user_prompt(
                query=query,
                context_chunks=prepare_context_chunks(context_chunks),
                history=history,
                general_only=general_only,
                draft_answer=draft_answer,
                query_type=query_type,
                user_level=user_level,
            ),
        },
    ]

    if settings.HF_MODEL_ENABLED and settings.HF_API_KEY and settings.GROQ_MODEL:
        try:
            answer = _generate_with_hf_router_chat(settings.GROQ_MODEL, messages)
            if answer:
                return answer, f"hf-router:{settings.GROQ_MODEL}"
        except Exception as exc:
            logger.warning("Primary routed generation failed: %s", exc)

    if settings.GROQ_MODEL_ENABLED and settings.GROQ_API_KEY and ":" not in (settings.GROQ_MODEL or ""):
        try:
            answer = _generate_with_groq_direct(messages)
            if answer:
                return answer, f"groq:{settings.GROQ_MODEL}"
        except Exception as exc:
            logger.warning("Direct Groq generation failed: %s", exc)

    if settings.HF_MODEL_ENABLED and settings.HF_API_KEY and settings.HF_MODEL:
        try:
            answer = _generate_with_hf_router_chat(settings.HF_MODEL, messages)
            if answer:
                return answer, f"hf-router:{settings.HF_MODEL}"
        except Exception as exc:
            logger.warning("Fallback routed generation failed: %s", exc)

    return None, None


def configured_provider_summary() -> dict[str, Any]:
    return {
        "primary_model": settings.GROQ_MODEL,
        "fallback_model": settings.HF_MODEL,
        "groq_configured": bool(settings.GROQ_API_KEY),
        "groq_enabled": bool(settings.GROQ_MODEL_ENABLED),
        "groq_model": settings.GROQ_MODEL,
        "hf_configured": bool(settings.HF_API_KEY),
        "hf_enabled": bool(settings.HF_MODEL_ENABLED),
        "hf_model": settings.HF_MODEL,
        "top_k": settings.RAG_TOP_K,
        "nvidia_rerank_enabled": bool(settings.NVIDIA_RERANK_ENABLED),
        "nvidia_rerank_configured": bool(settings.NVIDIA_RERANK_ENABLED and settings.NVIDIA_API_KEY),
        "nvidia_rerank_model": settings.NVIDIA_RERANK_MODEL,
        "nvidia_rerank_url": settings.NVIDIA_RERANK_URL,
    }
