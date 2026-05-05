from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from core.config import settings
from .embeddings import start_model_warmup
from .ev_catalog import load_documents, load_excel_as_documents
from .ev_chat_knowledge import (
    build_capabilities_answer,
    build_identity_answer,
    build_limitations_answer,
    build_policy_answer,
    extract_supporting_lines,
    is_capabilities_query,
    is_ev_concept_query,
    is_identity_query,
    is_limitations_query,
    is_location_query,
    is_policy_query,
    load_knowledge_articles,
    retrieve_knowledge_articles,
)
from .ev_chat_memory import apply_session_memory, build_session_memory, needs_recommendation_clarification
from .ev_chat_response import (
    build_clarification_answer,
    build_comparison_answer,
    build_inventory_answer,
    build_knowledge_answer,
    build_no_match_answer,
    build_out_of_domain_answer,
    build_recommendation_answer,
    build_spec_answer,
)
from .ev_chat_retrieval import (
    closest_vehicle_candidates,
    contains_vehicle_mention,
    hybrid_retrieve,
    normalize_text,
    resolve_named_vehicles,
    vehicle_aliases,
)
from .ev_rag_types import ChatAnswer, ParsedQuery, RetrievalMatch, VehicleDocument
from .faiss_store import FaissStore
from .llm import generate_chat_response
from .query_parser import parse_user_query
from .retrieval import station_answer


SMALLTALK_REPLIES = {
    "hi": "Hello! Ask me about EV recommendations, charging, subsidies, TCO, or a model comparison from the current India EV dataset.",
    "hii": "Hello! Ask me about EV recommendations, charging, subsidies, TCO, or a model comparison from the current India EV dataset.",
    "hie": "Hello! Ask me about EV recommendations, charging, subsidies, TCO, or a model comparison from the current India EV dataset.",
    "hello": "Hello! Ask me about EV recommendations, charging, subsidies, TCO, or a model comparison from the current India EV dataset.",
    "hey": "Hello! Ask me about EV recommendations, charging, subsidies, TCO, or a model comparison from the current India EV dataset.",
    "good morning": "Hello! Tell me your budget, segment, or use case and I’ll build a grounded EV shortlist.",
    "good evening": "Hello! Tell me your budget, segment, or use case and I’ll build a grounded EV shortlist.",
    "namaste": "Namaste! Ask me about EV models, charging, subsidies, TCO, or an India-focused comparison.",
    "thanks": "Happy to help. If you want, I can keep narrowing the shortlist from the current dataset.",
    "thank you": "Happy to help. If you want, I can keep narrowing the shortlist from the current dataset.",
}

OOD_HINTS = [
    "president",
    "prime minister",
    "cricket",
    "python code",
    "java code",
    "stock market",
    "weather",
]

SPEC_HINTS = [
    "price",
    "range",
    "battery",
    "charging",
    "top speed",
    "warranty",
    "motor",
    "spec",
    "specs",
]

STRICT_NO_DATA_MESSAGE = "Not enough data available"

COMPARISON_FOLLOW_UP_HINTS = (
    "comparison",
    "compare",
    "table",
    "tabular",
    "side by side",
    "side-by-side",
    "which is better",
    "which one is better",
    "better fit",
    "better buy",
    "difference",
    "same two",
    "those two",
    "these two",
    "both cars",
    "both models",
)


@dataclass
class KnowledgeBaseArtifacts:
    vehicles: list[VehicleDocument]
    faiss_store: FaissStore | None


class EVRAGService:
    def __init__(self) -> None:
        self._artifacts: KnowledgeBaseArtifacts | None = None
        self._articles = load_knowledge_articles()

    def load(self) -> None:
        if self._artifacts is not None:
            return

        json_path = Path(settings.EV_JSON_PATH)
        index_path = Path(settings.EV_FAISS_INDEX_PATH)
        meta_path = Path(settings.EV_FAISS_META_PATH)

        if json_path.exists():
            vehicles = load_documents(json_path)
        else:
            vehicles = load_excel_as_documents(settings.EV_EXCEL_PATH)

        store = None
        if index_path.exists() and meta_path.exists():
            try:
                store = FaissStore.load(index_path, meta_path)
            except Exception:
                store = None

        self._artifacts = KnowledgeBaseArtifacts(vehicles=vehicles, faiss_store=store)

    def warmup(self) -> None:
        try:
            start_model_warmup()
            self.load()
        except Exception:
            pass

    def reload(self) -> None:
        self._artifacts = None

    @property
    def artifacts(self) -> KnowledgeBaseArtifacts:
        self.load()
        if self._artifacts is None:
            raise RuntimeError("EV knowledge base is unavailable")
        return self._artifacts

    def answer(self, query: str, chat_history: list[dict[str, str]] | None = None) -> ChatAnswer:
        history = chat_history or []
        normalized = (query or "").strip().lower()

        if normalized in SMALLTALK_REPLIES:
            parsed = ParsedQuery(intent="info", rewritten_query=query)
            return ChatAnswer(answer=SMALLTALK_REPLIES[normalized], intent="info", parsed_query=parsed, matches=[], provider=None)

        if any(token in normalized for token in OOD_HINTS) and "ev" not in normalized and "electric" not in normalized:
            parsed = ParsedQuery(intent="info", rewritten_query=query)
            return ChatAnswer(answer=build_out_of_domain_answer(), intent="info", parsed_query=parsed, matches=[], provider=None)

        parsed = parse_user_query(query)
        memory = build_session_memory(history)
        parsed = apply_session_memory(query, parsed, memory)

        inventory_answer = self._inventory_answer(normalized)
        if inventory_answer:
            return ChatAnswer(answer=inventory_answer, intent="info", parsed_query=parsed, matches=[], provider=None)

        if is_identity_query(query):
            return ChatAnswer(answer=build_identity_answer(), intent="info", parsed_query=parsed, matches=[], provider=None)

        if is_capabilities_query(query):
            return ChatAnswer(answer=build_capabilities_answer(), intent="info", parsed_query=parsed, matches=[], provider=None)

        if is_limitations_query(query):
            return ChatAnswer(answer=build_limitations_answer(), intent="info", parsed_query=parsed, matches=[], provider=None)

        if is_location_query(query):
            return ChatAnswer(answer=station_answer(query), intent="info", parsed_query=parsed, matches=[], provider=None)

        if is_policy_query(query):
            return ChatAnswer(
                answer=build_policy_answer(query, parsed.filters.state),
                intent="info",
                parsed_query=parsed,
                matches=[],
                provider=None,
            )

        spec_match = self._spec_answer(query, parsed)
        if spec_match is None and re.search(r"\b(it|its|this|that|this one|that one)\b", normalized):
            spec_match = self._recent_vehicle_from_history(history)
        if spec_match is not None:
            vehicle = spec_match
            match = RetrievalMatch(vehicle=vehicle, score=1.0, matched_on=["name_exact", "spec"])
            fallback_answer = build_spec_answer(vehicle, parsed, query)
            return self._finalize_answer(
                query=query,
                parsed=parsed,
                history=history,
                matches=[match],
                fallback_answer=fallback_answer,
                context_chunks=self._vehicle_context_chunks([match], parsed),
                general_only=False,
            )

        if parsed.intent == "comparison":
            comparison_matches, clarification = self._comparison_matches(query)
            if clarification:
                follow_up_matches = self._follow_up_comparison_matches(query, parsed, history)
                if follow_up_matches:
                    comparison_matches = follow_up_matches
                    clarification = None
                else:
                    return ChatAnswer(answer=clarification, intent="comparison", parsed_query=parsed, matches=[], provider=None)
            parsed = parsed.model_copy(update={"vehicle_names": [match.vehicle.name for match in comparison_matches]})
            fallback_answer = build_comparison_answer(comparison_matches, parsed)
            return self._finalize_answer(
                query=query,
                parsed=parsed,
                history=history,
                matches=comparison_matches,
                fallback_answer=fallback_answer,
                context_chunks=self._vehicle_context_chunks(comparison_matches, parsed),
                general_only=False,
            )

        follow_up_comparison_matches = self._follow_up_comparison_matches(query, parsed, history)
        if follow_up_comparison_matches:
            parsed = parsed.model_copy(
                update={
                    "intent": "comparison",
                    "vehicle_names": [match.vehicle.name for match in follow_up_comparison_matches],
                }
            )
            fallback_answer = build_comparison_answer(follow_up_comparison_matches, parsed)
            return self._finalize_answer(
                query=query,
                parsed=parsed,
                history=history,
                matches=follow_up_comparison_matches,
                fallback_answer=fallback_answer,
                context_chunks=self._vehicle_context_chunks(follow_up_comparison_matches, parsed),
                general_only=False,
            )

        if parsed.intent == "info" and is_ev_concept_query(query) and not self._looks_like_vehicle_request(query):
            articles = retrieve_knowledge_articles(query, self._articles, top_k=settings.RAG_TOP_K)
            article = next(iter(articles), None)
            if not article:
                return ChatAnswer(answer=STRICT_NO_DATA_MESSAGE, intent="info", parsed_query=parsed, matches=[], provider=None)
            fallback_answer = build_knowledge_answer(query, article)
            return self._finalize_answer(
                query=query,
                parsed=parsed,
                history=history,
                matches=[],
                fallback_answer=fallback_answer,
                context_chunks=self._article_context_chunks(articles, query),
                general_only=not articles,
            )

        if needs_recommendation_clarification(query, parsed):
            return ChatAnswer(
                answer=build_clarification_answer(query, parsed),
                intent=parsed.intent,
                parsed_query=parsed,
                matches=[],
                provider=None,
                confidence="low",
            )

        matches = hybrid_retrieve(
            query=parsed.rewritten_query or query,
            parsed=parsed,
            vehicles=self.artifacts.vehicles,
            store=self.artifacts.faiss_store,
            top_k=settings.RAG_TOP_K,
        )
        if not matches:
            return ChatAnswer(answer=STRICT_NO_DATA_MESSAGE, intent=parsed.intent, parsed_query=parsed, matches=[], provider=None, confidence="low")

        if parsed.intent == "recommendation":
            fallback_answer = build_recommendation_answer(query, parsed, matches)
            return self._finalize_answer(
                query=query,
                parsed=parsed,
                history=history,
                matches=matches,
                fallback_answer=fallback_answer,
                context_chunks=self._vehicle_context_chunks(matches, parsed),
                general_only=False,
            )

        first = matches[0].vehicle
        fallback_answer = build_spec_answer(first, parsed, query)
        return self._finalize_answer(
            query=query,
            parsed=parsed,
            history=history,
            matches=[matches[0]],
            fallback_answer=fallback_answer,
            context_chunks=self._vehicle_context_chunks([matches[0]], parsed),
            general_only=False,
        )

    def inventory_summary(self) -> str:
        vehicles = self.artifacts.vehicles
        counts: dict[str, int] = {}
        for vehicle in vehicles:
            category = str(vehicle.metadata.get("category") or vehicle.vehicle_type or "EV")
            counts[category] = counts.get(category, 0) + 1
        return build_inventory_answer(len(vehicles), counts)

    def _inventory_answer(self, normalized_query: str) -> str | None:
        if any(phrase in normalized_query for phrase in ["list all ev", "all evs", "show all vehicles", "show all evs", "full list"]):
            return self.inventory_summary()
        return None

    def _spec_answer(self, query: str, parsed: ParsedQuery) -> VehicleDocument | None:
        if not any(token in (query or "").lower() for token in SPEC_HINTS):
            return None
        named = resolve_named_vehicles(query, self.artifacts.vehicles)
        if named:
            return named[0]
        return None

    def _recent_vehicle_from_history(self, chat_history: list[dict[str, str]]) -> VehicleDocument | None:
        user_messages = [
            item.get("content") or item.get("text") or ""
            for item in reversed(chat_history)
            if (item.get("role") or "").lower() in {"user", "assistant"}
        ]
        for message in user_messages:
            named = resolve_named_vehicles(message, self.artifacts.vehicles)
            if named:
                return named[0]
        return None

    def _comparison_matches(self, query: str) -> tuple[list[RetrievalMatch], str | None]:
        vehicles = self.artifacts.vehicles
        cleaned_query = re.sub(r"^\s*(compare|difference between)\s+", "", query, flags=re.IGNORECASE)
        requested_parts = re.split(r"\bvs\b|\bversus\b|\band\b|,", cleaned_query, flags=re.IGNORECASE)
        requested_parts = [part.strip(" ?.") for part in requested_parts if len(part.strip()) > 2]

        resolved: list[VehicleDocument] = []
        suggestions: list[str] = []
        for part in requested_parts[:2]:
            normalized_part = normalize_text(part)
            exact = [vehicle for vehicle in vehicles if normalized_part in vehicle_aliases(vehicle)]
            if not exact:
                exact = resolve_named_vehicles(part, vehicles)
            if len(exact) == 1:
                resolved.append(exact[0])
                continue

            close = closest_vehicle_candidates(part, vehicles, limit=2)
            suggestions.extend(vehicle.name for vehicle in close)

        if len(resolved) == 2:
            return [
                RetrievalMatch(vehicle=vehicle, score=1.0, matched_on=["name_exact", "comparison"])
                for vehicle in resolved
            ], None

        if suggestions:
            suggestion_text = ", ".join(dict.fromkeys(suggestions))
            clarification = (
                "I do not want to compare the wrong models, so I need the exact names from the current dataset.\n\n"
                f"Closest matches I found: {suggestion_text}."
            )
            return [], clarification

        return [], "I can compare EVs, but I need the exact two model names from the current dataset."

    def _follow_up_comparison_matches(
        self,
        query: str,
        parsed: ParsedQuery,
        history: list[dict[str, str]],
    ) -> list[RetrievalMatch]:
        normalized = normalize_text(query)
        if not any(hint in normalized for hint in COMPARISON_FOLLOW_UP_HINTS):
            return []

        recent_pair = self._recent_comparison_pair_from_history(history)
        if len(recent_pair) < 2:
            return []

        return [
            RetrievalMatch(vehicle=vehicle, score=1.0, matched_on=["history", "comparison_follow_up"])
            for vehicle in recent_pair[:2]
        ]

    def _recent_comparison_pair_from_history(self, chat_history: list[dict[str, str]]) -> list[VehicleDocument]:
        prioritized_history = sorted(
            enumerate(chat_history),
            key=lambda item: (0 if (item[1].get("role") or "").lower() == "user" else 1, -item[0]),
        )
        for _, item in prioritized_history:
            text = item.get("content") or item.get("text") or ""
            named = self._ordered_named_vehicles(text)
            if len(named) >= 2:
                return named[:2]
        return []

    def _ordered_named_vehicles(self, text: str) -> list[VehicleDocument]:
        normalized_text_value = normalize_text(text)
        named = resolve_named_vehicles(text, self.artifacts.vehicles)
        if len(named) < 2:
            return named

        def first_position(vehicle: VehicleDocument) -> int:
            positions = [
                normalized_text_value.find(alias)
                for alias in vehicle_aliases(vehicle)
                if alias and normalized_text_value.find(alias) >= 0
            ]
            return min(positions) if positions else 10**9

        return sorted(named, key=first_position)

    def _looks_like_vehicle_request(self, query: str) -> bool:
        q = (query or "").lower()
        if any(token in q for token in ["best", "recommend", "buy", "compare", "under ", "which ev"]):
            return True
        return any(contains_vehicle_mention(q, vehicle) for vehicle in self.artifacts.vehicles)

    def _finalize_answer(
        self,
        *,
        query: str,
        parsed: ParsedQuery,
        history: list[dict[str, str]],
        matches: list[RetrievalMatch],
        fallback_answer: str,
        context_chunks: list[str],
        general_only: bool,
    ) -> ChatAnswer:
        answer, provider = generate_chat_response(
            query=query,
            context_chunks=context_chunks,
            draft_answer=fallback_answer,
            history=history,
            general_only=general_only,
            query_type=parsed.query_type,
            user_level=parsed.user_level,
        )
        answer = self._validate_grounding(answer or fallback_answer, fallback_answer, context_chunks, matches)
        return ChatAnswer(
            answer=answer,
            intent=parsed.intent,
            parsed_query=parsed,
            matches=matches,
            provider=provider,
            confidence=self._confidence_level(parsed, matches),
        )

    def _vehicle_context_chunks(self, matches: list[RetrievalMatch], parsed: ParsedQuery) -> list[str]:
        chunks: list[str] = []
        for match in matches[: settings.RAG_TOP_K]:
            vehicle = match.vehicle
            details = [
                f"{vehicle.name} ({vehicle.vehicle_type})",
                vehicle.content,
                f"price ₹{vehicle.price_inr:,}" if vehicle.price_inr is not None else "price unavailable",
                f"range {vehicle.range_km} km" if vehicle.range_km is not None else "range unavailable",
                f"battery {vehicle.battery_kwh:.1f} kWh" if vehicle.battery_kwh is not None else "battery unavailable",
                f"charging {vehicle.charging_time}" if vehicle.charging_time else None,
                f"charging type {vehicle.charging_type}" if vehicle.charging_type else None,
            ]
            if vehicle.features:
                details.append("features: " + ", ".join(vehicle.features[:4]))
            if parsed.filters.state:
                details.append(f"state context: {parsed.filters.state}")
            chunks.append(". ".join(part for part in details if part))
        return chunks

    def _article_context_chunks(self, articles, query: str) -> list[str]:
        chunks: list[str] = []
        for article in articles[: settings.RAG_TOP_K]:
            support_lines = extract_supporting_lines(article, query, limit=2)
            if support_lines:
                chunks.append(f"{article.title}. " + " ".join(support_lines))
            else:
                chunks.append(f"{article.title}. {article.content[:320]}")
        return chunks

    def _build_general_no_context_answer(self, parsed: ParsedQuery) -> str:
        return STRICT_NO_DATA_MESSAGE

    def _validate_grounding(
        self,
        answer: str,
        fallback_answer: str,
        context_chunks: list[str],
        matches: list[RetrievalMatch],
    ) -> str:
        if not context_chunks and not matches:
            return STRICT_NO_DATA_MESSAGE

        supported_text = " ".join([fallback_answer, *context_chunks]).lower()
        answer_text = (answer or "").strip()
        if not answer_text:
            return fallback_answer

        vehicle_names = [match.vehicle.name for match in matches]
        unsupported_names = [
            name
            for name in re.findall(r"\b[A-Z][A-Za-z0-9+-]*(?:\s+[A-Z][A-Za-z0-9+-]*){1,4}\b", answer_text)
            if any(token in name.lower() for token in ["ev", "tata", "mg", "byd", "kia", "hyundai", "ather", "ola"])
            and name.lower() not in supported_text
        ]
        if unsupported_names:
            return fallback_answer

        for number in re.findall(r"\b\d+(?:\.\d+)?\b", answer_text):
            if number not in supported_text:
                return fallback_answer

        if vehicle_names and not any(name.lower() in answer_text.lower() for name in vehicle_names):
            return fallback_answer
        return answer_text

    def _confidence_level(self, parsed: ParsedQuery, matches: list[RetrievalMatch]) -> str:
        if not matches:
            return "low"
        if parsed.intent == "comparison":
            return "high" if len(matches) >= 2 else "low"
        if parsed.intent == "recommendation":
            has_category = bool(parsed.filters.vehicle_type)
            has_budget = parsed.filters.max_price_inr is not None or parsed.filters.min_price_inr is not None
            has_usage = bool(parsed.filters.use_cases) or parsed.filters.daily_distance_km is not None
            has_priority = bool(parsed.filters.priority or parsed.sort_by)
            if has_category and has_budget and (has_usage or has_priority):
                return "high"
            if has_category and has_budget:
                return "medium"
            return "low"
        return "high"


ev_rag_service = EVRAGService()
