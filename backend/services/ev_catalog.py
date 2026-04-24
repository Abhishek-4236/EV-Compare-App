from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

from .ev_rag_types import VehicleDocument


COLUMN_ALIASES = {
    "name": ["name", "vehicle_name"],
    "brand": ["brand", "maker", "manufacturer"],
    "model": ["model"],
    "vehicle_type": ["type", "vehicle_type", "body_type", "category"],
    "price_inr": ["price", "price_inr", "approx_price_inr", "ex_showroom_price"],
    "range_km": ["range", "range_km", "claimed_range"],
    "battery_kwh": ["battery", "battery_kwh", "battery_capacity"],
    "charging_time": ["charging_time", "charging time"],
    "charging_type": ["charging_type"],
    "features": ["features", "feature", "highlights"],
}


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [
        re.sub(r"[^a-z0-9]+", "_", str(col).lower().strip()).strip("_")
        for col in df.columns
    ]
    return df


def _pick_column(df: pd.DataFrame, canonical: str) -> str | None:
    aliases = COLUMN_ALIASES.get(canonical, [])
    for alias in aliases:
        normalized = re.sub(r"[^a-z0-9]+", "_", alias.lower().strip()).strip("_")
        if normalized in df.columns:
            return normalized
    return None


def _safe_str(value: object) -> str | None:
    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "null", "not applicable"}:
        return None
    return text


def _safe_int(value: object) -> int | None:
    text = _safe_str(value)
    if not text:
        return None
    text = text.replace(",", "")
    match = re.search(r"[-+]?\d+(?:\.\d+)?", text)
    if not match:
        return None
    return int(float(match.group(0)))


def _safe_float(value: object) -> float | None:
    text = _safe_str(value)
    if not text:
        return None
    text = text.replace(",", "")
    match = re.search(r"[-+]?\d+(?:\.\d+)?", text)
    if not match:
        return None
    return round(float(match.group(0)), 2)


def _split_features(value: object) -> list[str]:
    text = _safe_str(value)
    if not text:
        return []
    parts = re.split(r"[|,;/]+", text)
    return [item.strip() for item in parts if item.strip()]


def _normalize_vehicle_type(value: str | None) -> str:
    text = (value or "").lower()
    if any(token in text for token in ["commercial", "cargo", "mini truck", "truck", "delivery", "scv"]):
        return "commercial"
    if text == "passenger" or "e-rickshaw" in text:
        return "three_wheeler"
    if "scooter" in text:
        return "scooter"
    if "bike" in text or "motorcycle" in text:
        return "bike"
    if any(token in text for token in ["car", "suv", "sedan", "hatchback", "mpv", "cuv"]) or text == "4w":
        return "car"
    if text == "2w":
        return "bike"
    if text == "3w":
        return "three_wheeler"
    return text or "ev"


def load_excel_as_documents(excel_path: str | Path) -> list[VehicleDocument]:
    path = Path(excel_path)
    if not path.exists():
        raise FileNotFoundError(f"Excel dataset not found: {path}")

    df = _clean_columns(pd.read_excel(path))

    col_name = _pick_column(df, "name")
    col_brand = _pick_column(df, "brand")
    col_model = _pick_column(df, "model")
    col_type = _pick_column(df, "vehicle_type")
    col_price = _pick_column(df, "price_inr")
    col_range = _pick_column(df, "range_km")
    col_battery = _pick_column(df, "battery_kwh")
    col_charge_time = _pick_column(df, "charging_time")
    col_charge_type = _pick_column(df, "charging_type")
    col_features = _pick_column(df, "features")

    documents: list[VehicleDocument] = []
    for idx, row in df.iterrows():
        brand = _safe_str(row.get(col_brand)) if col_brand else None
        model = _safe_str(row.get(col_model)) if col_model else None
        fallback_name = " ".join(part for part in [brand, model] if part).strip()
        name = _safe_str(row.get(col_name)) if col_name else None
        full_name = name or fallback_name
        if not full_name:
            continue

        vehicle_type = _normalize_vehicle_type(_safe_str(row.get(col_type)) if col_type else None)
        features = _split_features(row.get(col_features)) if col_features else []

        metadata: dict[str, object] = {}
        for column, value in row.items():
            if column in {col_name, col_brand, col_model, col_type, col_price, col_range, col_battery, col_charge_time, col_charge_type, col_features}:
                continue
            cleaned = _safe_str(value)
            if cleaned is not None:
                metadata[column] = cleaned

        documents.append(
            VehicleDocument(
                id=f"{_slug(full_name)}-{idx}",
                name=full_name,
                brand=brand or full_name.split()[0],
                model=model or full_name,
                vehicle_type=vehicle_type,
                price_inr=_safe_int(row.get(col_price)) if col_price else None,
                range_km=_safe_int(row.get(col_range)) if col_range else None,
                battery_kwh=_safe_float(row.get(col_battery)) if col_battery else None,
                charging_time=_safe_str(row.get(col_charge_time)) if col_charge_time else None,
                charging_type=_safe_str(row.get(col_charge_type)) if col_charge_type else None,
                features=features,
                source_row=idx,
                metadata=metadata,
            )
        )

    return documents


def build_vehicle_text(vehicle: VehicleDocument) -> str:
    feature_text = ", ".join(vehicle.features) if vehicle.features else "No highlighted features listed"
    meta_text = ", ".join(f"{key}: {value}" for key, value in vehicle.metadata.items())
    return (
        f"Vehicle: {vehicle.name}. "
        f"Brand: {vehicle.brand}. "
        f"Type: {vehicle.vehicle_type}. "
        f"Price: ₹{vehicle.price_inr or 'unknown'}. "
        f"Range: {vehicle.range_km or 'unknown'} km. "
        f"Battery: {vehicle.battery_kwh or 'unknown'} kWh. "
        f"Charging time: {vehicle.charging_time or 'unknown'}. "
        f"Charging type: {vehicle.charging_type or 'unknown'}. "
        f"Features: {feature_text}. "
        + (f"Extra details: {meta_text}." if meta_text else "")
    )


def save_documents(documents: list[VehicleDocument], json_path: str | Path) -> None:
    path = Path(json_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps([document.model_dump() for document in documents], indent=2),
        encoding="utf-8",
    )


def load_documents(json_path: str | Path) -> list[VehicleDocument]:
    path = Path(json_path)
    if not path.exists():
        raise FileNotFoundError(f"Vehicle JSON not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    return [VehicleDocument.model_validate(item) for item in data]
