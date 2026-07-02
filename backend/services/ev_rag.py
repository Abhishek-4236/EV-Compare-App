from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from sqlalchemy.orm import Session

from core.config import settings
from models import Vehicle
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
from .query_parser import parse_user_query, requires_ev_tools
from .retrieval import station_answer
from .ev_tools import tool_compare_vehicles, tool_get_subsidies, tool_get_vehicles
from .ev_answer_safety import confidence_level, validate_grounding


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
NO_VERIFIED_DATA_MESSAGE = "I don't have verified data for that model yet."

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

    def answer(
        self,
        query: str,
        chat_history: list[dict[str, str]] | None = None,
        *,
        db: Session | None = None,
    ) -> ChatAnswer:
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

        if db is not None and requires_ev_tools(query, parsed.intent):
            tool_answer = self._tool_first_answer(query=query, parsed=parsed, history=history, db=db)
            if tool_answer is not None:
                return tool_answer

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

    def _format_inr(self, value: int | None) -> str:
        if value is None:
            return "Unavailable"
        if value >= 100000:
            return f"₹{value / 100000:.2f} lakh"
        return f"₹{value:,}"

    def _db_vehicle_id_for_doc(self, db: Session, vehicle: VehicleDocument) -> int | None:
        row = db.query(Vehicle).filter(Vehicle.brand == vehicle.brand, Vehicle.model == vehicle.model).first()
        return int(row.id) if row else None

    def _vehicle_doc_from_db(self, row: Vehicle) -> VehicleDocument:
        name = f"{row.brand} {row.model}".strip()
        return VehicleDocument(
            id=str(row.id),
            content=None,
            name=name,
            brand=row.brand,
            model=row.model,
            vehicle_type=str(row.vehicle_type or row.category or "EV"),
            price_inr=int(row.approx_price_inr) if row.approx_price_inr is not None else None,
            range_km=int(row.range_km) if row.range_km is not None else None,
            battery_kwh=float(row.battery_kwh or 0) if row.battery_kwh is not None else None,
            charging_time=None,
            charging_type=str(row.charging_type) if row.charging_type else None,
            features=[],
            source_row=0,
            metadata={"category": row.category, "segment": str(row.segment)},
        )

    def _tool_first_answer(
        self,
        *,
        query: str,
        parsed: ParsedQuery,
        history: list[dict[str, str]],
        db: Session,
    ) -> ChatAnswer | None:
        normalized = (query or "").lower()

        # Comparison: resolve 2 vehicles, map to DB ids, then compute via tool.
        if parsed.intent == "comparison":
            comparison_matches, clarification = self._comparison_matches(query)
            if clarification:
                follow_up_matches = self._follow_up_comparison_matches(query, parsed, history)
                if follow_up_matches:
                    comparison_matches = follow_up_matches
                else:
                    return ChatAnswer(
                        answer=clarification,
                        intent="comparison",
                        parsed_query=parsed,
                        matches=[],
                        provider=None,
                        confidence="low",
                    )

            ids: list[int] = []
            db_docs: list[VehicleDocument] = []
            for match in comparison_matches[:2]:
                vid = self._db_vehicle_id_for_doc(db, match.vehicle)
                if not vid:
                    return ChatAnswer(
                        answer=NO_VERIFIED_DATA_MESSAGE,
                        intent="comparison",
                        parsed_query=parsed,
                        matches=[],
                        provider=None,
                        confidence="low",
                    )
                ids.append(vid)
                row = db.query(Vehicle).filter(Vehicle.id == vid).first()
                if row:
                    db_docs.append(self._vehicle_doc_from_db(row))

            tool = tool_compare_vehicles(db, ids=ids)
            if not tool.ok:
                return ChatAnswer(
                    answer=STRICT_NO_DATA_MESSAGE,
                    intent="comparison",
                    parsed_query=parsed,
                    matches=[],
                    provider=None,
                    confidence="low",
                )

            vehicles = (tool.data or {}).get("vehicles") or []
            if len(vehicles) < 2:
                return ChatAnswer(
                    answer=STRICT_NO_DATA_MESSAGE,
                    intent="comparison",
                    parsed_query=parsed,
                    matches=[],
                    provider=None,
                    confidence="low",
                )

            left, right = vehicles[0], vehicles[1]
            table = [
                f"| Feature | {left.get('name')} | {right.get('name')} |",
                "|---|---|---|",
                f"| Approx price | {self._format_inr(left.get('approx_price_inr'))} | {self._format_inr(right.get('approx_price_inr'))} |",
                f"| Range | {left.get('range_km', 'Unavailable')} km | {right.get('range_km', 'Unavailable')} km |",
                f"| Battery | {left.get('battery_kwh', 'Unavailable')} kWh | {right.get('battery_kwh', 'Unavailable')} kWh |",
                f"| Top speed | {left.get('top_speed_kmh', 'Unavailable')} km/h | {right.get('top_speed_kmh', 'Unavailable')} km/h |",
                f"| Charging type | {left.get('charging_type', 'Unavailable')} | {right.get('charging_type', 'Unavailable')} |",
                f"| Rating | {left.get('overall_rating', 'Unavailable')} | {right.get('overall_rating', 'Unavailable')} |",
                f"| Central subsidy (model) | {self._format_inr(left.get('fame2_subsidy_inr'))} | {self._format_inr(right.get('fame2_subsidy_inr'))} |",
                f"| Cost efficiency | {left.get('cost_efficiency', 'Unavailable')} | {right.get('cost_efficiency', 'Unavailable')} |",
                f"| Value score | {left.get('value_score', 'Unavailable')} | {right.get('value_score', 'Unavailable')} |",
            ]
            draft = "\n".join(
                [
                    "Here’s the grounded side-by-side from the current EViq database:",
                    "",
                    *table,
                    "",
                    "Tell me what matters most (price, range, charging, or performance) and I’ll call the better fit.",
                ]
            )
            context_chunks = [
                f"compare_vehicles result: {left.get('name')} price {left.get('approx_price_inr')} range {left.get('range_km')} battery {left.get('battery_kwh')} value_score {left.get('value_score')}",
                f"compare_vehicles result: {right.get('name')} price {right.get('approx_price_inr')} range {right.get('range_km')} battery {right.get('battery_kwh')} value_score {right.get('value_score')}",
            ]
            matches = [
                RetrievalMatch(vehicle=db_docs[0], score=1.0, matched_on=["tool:compare_vehicles"]) if len(db_docs) > 0 else None,
                RetrievalMatch(vehicle=db_docs[1], score=1.0, matched_on=["tool:compare_vehicles"]) if len(db_docs) > 1 else None,
            ]
            matches = [m for m in matches if m is not None]
            parsed = parsed.model_copy(update={"vehicle_names": [left.get("name") or "", right.get("name") or ""]})
            return self._finalize_answer(
                query=query,
                parsed=parsed,
                history=history,
                matches=matches,
                fallback_answer=draft,
                context_chunks=context_chunks,
                general_only=False,
            )

        # Model-specific price/subsidy/TCO/specs: use DB row when a vehicle is mentioned.
        named = resolve_named_vehicles(query, self.artifacts.vehicles)
        primary = named[0] if named else None

        financial = any(token in normalized for token in ["price", "on-road", "on road", "subsidy", "tco", "running cost", "cost/km"])
        if financial and primary is not None:
            vid = self._db_vehicle_id_for_doc(db, primary)
            if not vid:
                return ChatAnswer(answer=NO_VERIFIED_DATA_MESSAGE, intent=parsed.intent, parsed_query=parsed, matches=[], provider=None, confidence="low")
            if not parsed.filters.state:
                return ChatAnswer(
                    answer="Which state are you registering in (e.g., Delhi, Maharashtra)?",
                    intent="info",
                    parsed_query=parsed,
                    matches=[],
                    provider=None,
                    confidence="low",
                )
            daily_km = int(parsed.filters.daily_distance_km or 30)
            tool = tool_get_subsidies(db, vehicle_id=vid, state=parsed.filters.state, daily_km=daily_km)
            if not tool.ok:
                return ChatAnswer(answer=STRICT_NO_DATA_MESSAGE, intent="info", parsed_query=parsed, matches=[], provider=None, confidence="low")

            row = db.query(Vehicle).filter(Vehicle.id == vid).first()
            if not row:
                return ChatAnswer(answer=NO_VERIFIED_DATA_MESSAGE, intent="info", parsed_query=parsed, matches=[], provider=None, confidence="low")
            doc = self._vehicle_doc_from_db(row)

            approx_price = int(row.approx_price_inr or 0)
            total_sub = int(tool.data.get("total_applicable_subsidies") or 0)
            effective = max(0, approx_price - total_sub)

            draft = "\n".join(
                [
                    f"For {doc.name} in {parsed.filters.state.title()}, here’s the grounded subsidy + TCO snapshot (daily usage: {daily_km} km/day):",
                    "",
                    f"- Listed price (approx): {self._format_inr(approx_price)}",
                    f"- Central subsidy (applicable): {self._format_inr(int(tool.data.get('central_subsidy_inr') or 0))}",
                    f"- State subsidy (applicable): {self._format_inr(int(tool.data.get('state_subsidy_inr') or 0))}",
                    f"- Total applicable subsidies: {self._format_inr(total_sub)}",
                    f"- Effective price after subsidies (indicative): {self._format_inr(effective)}",
                    f"- 5-year TCO estimate (app formula): {self._format_inr(int(tool.data.get('tco_5year_inr') or 0))}",
                    "",
                    "If you share your actual monthly km and charging tariff, I can tighten the running-cost estimate further.",
                ]
            )
            context_chunks = [
                f"get_subsidies result for vehicle_id {vid} state {parsed.filters.state}: central {tool.data.get('central_subsidy_inr')} state_sub {tool.data.get('state_subsidy_inr')} total {tool.data.get('total_applicable_subsidies')} tco_5year {tool.data.get('tco_5year_inr')}",
                f"vehicle: {doc.name} price {approx_price} range {doc.range_km} battery {doc.battery_kwh}",
            ]
            match = RetrievalMatch(vehicle=doc, score=1.0, matched_on=["tool:get_subsidies"])
            return self._finalize_answer(
                query=query,
                parsed=parsed,
                history=history,
                matches=[match],
                fallback_answer=draft,
                context_chunks=context_chunks,
                general_only=False,
            )

        # Recommendation: use DB vehicles list tool first.
        if parsed.intent == "recommendation":
            category_map = {
                "scooter": "2W",
                "bike": "2W",
                "car": "4W",
                "three_wheeler": "3W",
                "truck": "Truck",
                "bus": "Bus",
                "commercial": None,
            }
            category = category_map.get(parsed.filters.vehicle_type or "", None)

            # Preserve existing app behavior expectations:
            # - Budget queries default to low price first
            # - Priority=price sorts ascending by price
            # - Priority=range sorts descending by range
            # - Priority=performance sorts by top speed proxy
            priority = parsed.filters.priority or parsed.sort_by
            if priority == "price":
                sort_by, sort_order = "approx_price_inr", "ASC"
            elif priority == "range":
                sort_by, sort_order = "range_km", "DESC"
            elif priority == "performance":
                sort_by, sort_order = "top_speed_kmh", "DESC"
            else:
                sort_by = "approx_price_inr" if parsed.filters.max_price_inr is not None else "overall_rating"
                sort_order = "ASC" if sort_by == "approx_price_inr" else "DESC"

            tool = tool_get_vehicles(
                db,
                category=category,
                brand=parsed.filters.brand,
                min_price=parsed.filters.min_price_inr,
                max_price=parsed.filters.max_price_inr,
                min_range=parsed.filters.min_range_km,
                charging_type=parsed.filters.charging_type,
                sort_by=sort_by,  # type: ignore[arg-type]
                sort_order=sort_order,  # type: ignore[arg-type]
                page=1,
                limit=max(5, settings.RAG_TOP_K),
            )
            vehicles = (tool.data or {}).get("vehicles") or []
            if not vehicles:
                return None

            def normalize_vehicle_type(v: dict) -> str:
                cat = (v.get("category") or "").upper()
                vt = (v.get("vehicle_type") or "").lower()
                if cat == "4W":
                    return "car"
                if cat == "3W":
                    return "three_wheeler"
                if cat == "TRUCK":
                    return "truck"
                if cat == "BUS":
                    return "bus"
                if cat == "2W":
                    return "scooter" if "scooter" in vt else "bike"
                return (v.get("vehicle_type") or "EV") or "EV"

            matches: list[RetrievalMatch] = []
            context_chunks: list[str] = []
            for v in vehicles[: settings.RAG_TOP_K]:
                name = (v.get("name") or "").strip()
                brand = (v.get("brand") or "").strip()
                model = (v.get("model") or "").strip()
                doc = VehicleDocument(
                    id=str(v.get("id") or ""),
                    content=None,
                    name=name,
                    brand=brand,
                    model=model,
                    vehicle_type=normalize_vehicle_type(v),
                    price_inr=int(v.get("approx_price_inr")) if v.get("approx_price_inr") is not None else None,
                    range_km=int(v.get("range_km")) if v.get("range_km") is not None else None,
                    battery_kwh=float(v.get("battery_kwh")) if v.get("battery_kwh") is not None else None,
                    charging_time=None,
                    charging_type=str(v.get("charging_type")) if v.get("charging_type") else None,
                    features=[],
                    source_row=0,
                    metadata={"category": v.get("category")},
                )
                matches.append(RetrievalMatch(vehicle=doc, score=1.0, matched_on=["tool:get_vehicles"]))
                context_chunks.append(
                    f"get_vehicles result: {name} type {doc.vehicle_type} price {doc.price_inr} range {doc.range_km} battery {doc.battery_kwh} charging_type {doc.charging_type} rating {v.get('overall_rating')}"
                )

            draft = build_recommendation_answer(query, parsed, matches)
            if not draft.strip().endswith("Pro-Tip:"):
                draft = "\n".join(
                    [
                        draft.rstrip(),
                        "",
                        "Pro-Tip: If home charging is available, set a conservative daily charge limit (like 80–90%) and reserve 100% only for long trips.",
                    ]
                )

            return self._finalize_answer(
                query=query,
                parsed=parsed,
                history=history,
                matches=matches,
                fallback_answer=draft,
                context_chunks=context_chunks,
                general_only=False,
            )

        return None

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
        answer = validate_grounding(answer or fallback_answer, fallback_answer, context_chunks, matches)
        return ChatAnswer(
            answer=answer,
            intent=parsed.intent,
            parsed_query=parsed,
            matches=matches,
            provider=provider,
            confidence=confidence_level(parsed, matches),
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

ev_rag_service = EVRAGService()
