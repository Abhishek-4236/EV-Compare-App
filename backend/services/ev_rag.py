from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from core.config import settings
from .embeddings import start_model_warmup
from .ev_catalog import load_documents, load_excel_as_documents
from .ev_chat_knowledge import (
    build_limitations_answer,
    build_policy_answer,
    is_ev_concept_query,
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
            return ChatAnswer(answer=SMALLTALK_REPLIES[normalized], intent="info", parsed_query=parsed, matches=[])

        if any(token in normalized for token in OOD_HINTS) and "ev" not in normalized and "electric" not in normalized:
            parsed = ParsedQuery(intent="info", rewritten_query=query)
            return ChatAnswer(answer=build_out_of_domain_answer(), intent="info", parsed_query=parsed, matches=[])

        parsed = parse_user_query(query)
        memory = build_session_memory(history)
        parsed = apply_session_memory(query, parsed, memory)

        inventory_answer = self._inventory_answer(normalized)
        if inventory_answer:
            return ChatAnswer(answer=inventory_answer, intent="info", parsed_query=parsed, matches=[])

        if is_limitations_query(query):
            return ChatAnswer(answer=build_limitations_answer(), intent="info", parsed_query=parsed, matches=[])

        if is_location_query(query):
            return ChatAnswer(answer=station_answer(query), intent="info", parsed_query=parsed, matches=[])

        if is_policy_query(query):
            return ChatAnswer(
                answer=build_policy_answer(query, parsed.filters.state),
                intent="info",
                parsed_query=parsed,
                matches=[],
            )

        spec_match = self._spec_answer(query, parsed)
        if spec_match is None and re.search(r"\b(it|its|this|that|this one|that one)\b", normalized):
            spec_match = self._recent_vehicle_from_history(history)
        if spec_match is not None:
            vehicle = spec_match
            answer = build_spec_answer(vehicle, parsed, query)
            match = RetrievalMatch(vehicle=vehicle, score=1.0, matched_on=["name_exact", "spec"])
            return ChatAnswer(answer=answer, intent="info", parsed_query=parsed, matches=[match])

        if parsed.intent == "comparison":
            comparison_matches, clarification = self._comparison_matches(query)
            if clarification:
                return ChatAnswer(answer=clarification, intent="comparison", parsed_query=parsed, matches=[])
            answer = build_comparison_answer(comparison_matches, parsed)
            return ChatAnswer(answer=answer, intent="comparison", parsed_query=parsed, matches=comparison_matches)

        if parsed.intent == "info" and is_ev_concept_query(query) and not self._looks_like_vehicle_request(query):
            article = next(iter(retrieve_knowledge_articles(query, self._articles, top_k=1)), None)
            return ChatAnswer(
                answer=build_knowledge_answer(query, article),
                intent="info",
                parsed_query=parsed,
                matches=[],
            )

        if needs_recommendation_clarification(query, parsed):
            return ChatAnswer(
                answer=build_clarification_answer(query, parsed),
                intent=parsed.intent,
                parsed_query=parsed,
                matches=[],
            )

        matches = hybrid_retrieve(
            query=parsed.rewritten_query or query,
            parsed=parsed,
            vehicles=self.artifacts.vehicles,
            store=self.artifacts.faiss_store,
            top_k=5,
        )
        if not matches:
            return ChatAnswer(
                answer=build_no_match_answer(parsed),
                intent=parsed.intent,
                parsed_query=parsed,
                matches=[],
            )

        if parsed.intent == "recommendation":
            answer = build_recommendation_answer(query, parsed, matches)
            return ChatAnswer(answer=answer, intent="recommendation", parsed_query=parsed, matches=matches)

        first = matches[0].vehicle
        answer = build_spec_answer(first, parsed, query)
        return ChatAnswer(answer=answer, intent="info", parsed_query=parsed, matches=[matches[0]])

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
            if (item.get("role") or "").lower() == "user"
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

    def _looks_like_vehicle_request(self, query: str) -> bool:
        q = (query or "").lower()
        if any(token in q for token in ["best", "recommend", "buy", "compare", "under ", "which ev"]):
            return True
        return any(contains_vehicle_mention(q, vehicle) for vehicle in self.artifacts.vehicles)


ev_rag_service = EVRAGService()
