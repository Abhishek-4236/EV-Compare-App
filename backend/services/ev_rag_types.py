from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


ChatIntent = Literal["recommendation", "comparison", "info"]


class VehicleDocument(BaseModel):
    id: str
    name: str
    brand: str
    model: str
    vehicle_type: str
    price_inr: int | None = None
    range_km: int | None = None
    battery_kwh: float | None = None
    charging_time: str | None = None
    charging_type: str | None = None
    features: list[str] = Field(default_factory=list)
    source_row: int
    metadata: dict[str, Any] = Field(default_factory=dict)


class QueryFilters(BaseModel):
    min_price_inr: int | None = None
    max_price_inr: int | None = None
    min_range_km: int | None = None
    vehicle_type: str | None = None
    brand: str | None = None
    charging_type: str | None = None
    fast_charging: bool | None = None
    state: str | None = None
    daily_distance_km: int | None = None
    home_charging: bool | None = None
    use_cases: list[str] = Field(default_factory=list)


class ParsedQuery(BaseModel):
    intent: ChatIntent = "info"
    rewritten_query: str
    filters: QueryFilters = Field(default_factory=QueryFilters)
    vehicle_names: list[str] = Field(default_factory=list)
    sort_by: str | None = None
    user_goal: str | None = None


class RetrievalMatch(BaseModel):
    vehicle: VehicleDocument
    score: float
    matched_on: list[str] = Field(default_factory=list)


class ChatAnswer(BaseModel):
    answer: str
    intent: ChatIntent
    parsed_query: ParsedQuery
    matches: list[RetrievalMatch] = Field(default_factory=list)
    provider: str | None = None
