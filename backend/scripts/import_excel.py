import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import text

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Base, SessionLocal, engine
from models import ChatFeedback, ChatSession, Vehicle
from services.embeddings import embed_texts
from services.ev_catalog import save_documents
from services.ev_rag_types import VehicleDocument
from services.faiss_store import FaissStore

RAW_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "raw"
PROCESSED_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
IMPORT_STATE_PATH = PROCESSED_DATA_DIR / "import_state.json"

# Excel column name (after clean) -> model field
COLUMN_MAP = {
    "category": "category",
    "vehicle_type": "vehicle_type",
    "brand": "brand",
    "model": "model",
    "approx_price_inr": "approx_price_inr",
    "range_km": "range_km",
    "battery_kwh": "battery_kwh",
    "top_speed": "top_speed_kmh",
    "charging_time": "charging_time_ac_hrs",
    "charging_type": "charging_type",
    "market_status": "market_status",
    "safety_rating": "safety_rating",
    "vehicle_warranty": "warranty_years",
}

CATEGORY_MAP = {
    "2w": "2W",
    "scooter": "2W",
    "bike": "2W",
    "motorcycle": "2W",
    "4w": "4W",
    "car": "4W",
    "3w": "3W",
    "3-wheeler": "3W",
    "auto": "3W",
    "bus": "Bus",
    "truck": "Truck",
}

SEGMENT_MAP = {
    "2W": "TWO_WHEELER",
    "3W": "THREE_WHEELER",
    "4W": "FOUR_WHEELER",
    "Truck": "TRUCK",
    "Bus": "BUS",
}


def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [
        re.sub(r"[^a-z0-9]+", "_", str(column).lower().strip()).strip("_")
        for column in df.columns
    ]
    return df


def safe_str(value):
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    text = str(value).strip()
    return text if text and text.lower() not in {"nan", "none", "null", ""} else None


def _extract_numbers(value) -> list[float]:
    text = safe_str(value)
    if not text:
        return []
    matches = re.findall(r"[-+]?\d+(?:\.\d+)?", text.replace(",", ""))
    return [float(match) for match in matches]


def safe_int(value, *, prefer: str = "first"):
    numbers = _extract_numbers(value)
    if not numbers:
        return None
    if prefer == "min":
        selected = min(numbers)
    elif prefer == "max":
        selected = max(numbers)
    else:
        selected = numbers[0]
    return int(round(selected))


def safe_float(value, *, prefer: str = "first"):
    numbers = _extract_numbers(value)
    if not numbers:
        return None
    if prefer == "min":
        selected = min(numbers)
    elif prefer == "max":
        selected = max(numbers)
    else:
        selected = numbers[0]
    return round(float(selected), 2)


def parse_warranty_years(value):
    return safe_int(value)


def parse_charging_hours(value):
    return safe_float(value, prefer="min")


def normalize_category(value: str | None) -> str:
    raw_category = (value or "").strip()
    lowered = raw_category.lower()
    for key, mapped in CATEGORY_MAP.items():
        if key in lowered:
            return mapped
    return raw_category or "4W"


def normalize_vehicle_type(value: str | None, category: str) -> str:
    text = (value or "").strip().lower()
    if any(token in text for token in ["commercial", "cargo", "mini truck", "truck", "delivery", "scv"]):
        return "commercial"
    if "passenger" in text and category == "3W":
        return "three_wheeler"
    if "scooter" in text:
        return "scooter"
    if "bike" in text or "motorcycle" in text:
        return "bike"
    if any(token in text for token in ["car", "suv", "sedan", "hatchback", "mpv", "cuv"]):
        return "car"
    if category == "2W":
        return "bike"
    if category == "3W":
        return "three_wheeler"
    if category == "4W":
        return "car"
    if category == "Bus":
        return "bus"
    if category == "Truck":
        return "truck"
    return text or "ev"


def build_missing_model_name(category: str | None, vehicle_type: str | None) -> str:
    category_text = safe_str(category)
    vehicle_type_text = safe_str(vehicle_type)
    descriptor = None

    if category_text in {"Truck", "Bus"}:
        descriptor = category_text
    elif vehicle_type_text and vehicle_type_text.lower() != "commercial":
        descriptor = vehicle_type_text.title()
    elif category_text:
        descriptor = category_text
    else:
        descriptor = "EV"

    if not descriptor.lower().endswith("ev"):
        descriptor = f"{descriptor} EV"
    return f"Unnamed {descriptor}"


def build_vehicle_text(core_data: dict, extra_info: dict[str, str]) -> str:
    extra_text = ", ".join(f"{key}: {value}" for key, value in extra_info.items())
    return (
        f"{core_data['brand']} {core_data['model']}. "
        f"Category: {core_data['category']}. Segment: {core_data['segment']}. "
        f"Type: {core_data.get('vehicle_type') or 'unknown'}. "
        f"Price: ₹{core_data['approx_price_inr']}. "
        f"Range: {core_data['range_km']} km. "
        f"Battery: {core_data['battery_kwh']} kWh. "
        f"Charging: {core_data.get('charging_type') or 'unknown'}. "
        f"Top speed: {core_data.get('top_speed_kmh') or 'unknown'} kmh. "
        + (f"Details: {extra_text}." if extra_text else "")
    )


def ensure_runtime_schema():
    statements = [
        "ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS extra_info JSONB",
        "ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS user_id INTEGER",
        "ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS title VARCHAR(200) DEFAULT 'New Chat'",
        "ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS lessons_learned TEXT",
    ]

    with engine.begin() as conn:
        for statement in statements:
            conn.execute(text(statement))


def get_available_dataset_files() -> list[Path]:
    if not RAW_DATA_DIR.exists():
        return []
    return sorted(
        [path for path in RAW_DATA_DIR.glob("*.xlsx") if not path.name.startswith("~$")],
        key=lambda path: (path.stat().st_mtime, path.stat().st_size, path.name),
        reverse=True,
    )


def get_preferred_dataset_path() -> Path | None:
    files = get_available_dataset_files()
    if not files:
        return None

    for preferred_name in ("latest_upload_import.xlsx", "India_EV_All_Segments_Dataset_2026_filled.xlsx"):
        for file_path in files:
            if file_path.name == preferred_name:
                return file_path
    return files[0]


def get_dataset_signature(data_path: Path) -> str:
    stat = data_path.stat()
    return f"{data_path.name}:{stat.st_size}:{stat.st_mtime_ns}"


def read_import_state() -> dict | None:
    if not IMPORT_STATE_PATH.exists():
        return None
    try:
        return json.loads(IMPORT_STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return None


def write_import_state(state: dict) -> None:
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    IMPORT_STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")


def prepare_rows(df: pd.DataFrame) -> tuple[list[dict], int]:
    prepared_rows: list[dict] = []
    skipped = 0

    for idx, row in df.iterrows():
        try:
            core_data: dict[str, object] = {}
            extra_info: dict[str, str] = {}

            for column, value in row.items():
                if column in COLUMN_MAP:
                    core_data[COLUMN_MAP[column]] = value
                else:
                    cleaned = safe_str(value)
                    if cleaned is not None:
                        extra_info[column.replace("_", " ").title()] = cleaned

            normalized_category = normalize_category(safe_str(core_data.get("category")))
            core_data["category"] = normalized_category
            core_data["segment"] = SEGMENT_MAP.get(normalized_category, "FOUR_WHEELER")

            brand = safe_str(core_data.get("brand"))
            model = safe_str(core_data.get("model"))
            if not brand and model:
                brand = model.split()[0]
                extra_info["Source Brand Status"] = "Missing in source sheet"
            if not model and brand:
                model = build_missing_model_name(normalized_category, safe_str(core_data.get("vehicle_type")))
                extra_info["Source Model Status"] = "Missing in source sheet"

            core_data["brand"] = brand
            core_data["model"] = model
            core_data["approx_price_inr"] = safe_int(core_data.get("approx_price_inr"))
            core_data["range_km"] = safe_int(core_data.get("range_km"), prefer="min")
            core_data["battery_kwh"] = safe_float(core_data.get("battery_kwh"))
            core_data["top_speed_kmh"] = safe_int(core_data.get("top_speed_kmh"))
            core_data["safety_rating"] = safe_int(core_data.get("safety_rating"))
            core_data["vehicle_type"] = safe_str(core_data.get("vehicle_type"))
            core_data["charging_type"] = safe_str(core_data.get("charging_type"))
            core_data["market_status"] = safe_str(core_data.get("market_status")) or "Available"
            core_data["warranty_years"] = parse_warranty_years(core_data.get("warranty_years"))
            core_data["charging_time_ac_hrs"] = parse_charging_hours(core_data.get("charging_time_ac_hrs"))

            if len(_extract_numbers(row.get("range_km"))) > 1:
                extra_info["Range Display"] = safe_str(row.get("range_km")) or ""

            if not safe_str(core_data.get("brand")) or not safe_str(core_data.get("model")):
                print(f"  [SKIP] Row {idx}: missing brand/model")
                skipped += 1
                continue

            missing_required = next(
                (
                    field
                    for field in ("approx_price_inr", "range_km", "battery_kwh")
                    if core_data.get(field) is None
                ),
                None,
            )
            if missing_required:
                print(f"  [SKIP] Row {idx}: missing {missing_required}")
                skipped += 1
                continue

            vehicle_type = normalize_vehicle_type(
                safe_str(core_data.get("vehicle_type")),
                normalized_category,
            )
            document_metadata = {
                "category": normalized_category,
                "market_status": core_data.get("market_status"),
                "charging_type": core_data.get("charging_type"),
                **extra_info,
            }

            prepared_rows.append(
                {
                    "row_index": idx,
                    "core_data": core_data,
                    "extra_info": extra_info,
                    "vehicle_text": build_vehicle_text(core_data, extra_info),
                    "document": VehicleDocument(
                        id=f"{brand.lower().replace(' ', '-')}-{idx}",
                        name=f"{core_data['brand']} {core_data['model']}",
                        brand=core_data["brand"],
                        model=core_data["model"],
                        vehicle_type=vehicle_type,
                        price_inr=core_data["approx_price_inr"],
                        range_km=core_data["range_km"],
                        battery_kwh=float(core_data["battery_kwh"]),
                        charging_time=safe_str(row.get("charging_time")),
                        charging_type=core_data.get("charging_type"),
                        features=[],
                        source_row=idx,
                        metadata=document_metadata,
                    ),
                }
            )
        except Exception as exc:
            print(f"  [WARN] Row {idx} error: {exc}")
            skipped += 1

    return prepared_rows, skipped


def build_rag_artifacts(documents: list[VehicleDocument], embeddings: list[list[float]] | None) -> bool:
    save_documents(documents, PROCESSED_DATA_DIR / "vehicles.json")
    if not embeddings:
        for stale_path in (
            PROCESSED_DATA_DIR / "vehicles.faiss",
            PROCESSED_DATA_DIR / "vehicles.meta.json",
        ):
            if stale_path.exists():
                stale_path.unlink()
        return False

    store = FaissStore.build(vectors=embeddings, ids=[document.id for document in documents])
    store.save(PROCESSED_DATA_DIR / "vehicles.faiss", PROCESSED_DATA_DIR / "vehicles.meta.json")
    return True


def run_import(dataset_path: Path | None = None, refresh_rag_artifacts: bool = True) -> dict:
    data_path = dataset_path or get_preferred_dataset_path()
    if data_path is None:
        message = f"[ERROR] No Excel files found at {RAW_DATA_DIR}"
        print(message)
        return {"success": False, "message": message}

    print(f"Reading: {data_path.name}")
    df = pd.read_excel(data_path)
    print(f"Rows in Excel: {len(df)}")

    df = clean_column_names(df)
    print(f"Columns: {list(df.columns)}\n")

    prepared_rows, skipped = prepare_rows(df)
    vehicle_texts = [item["vehicle_text"] for item in prepared_rows]
    documents = [item["document"] for item in prepared_rows]

    print("Generating local embeddings in batch...")
    try:
        embeddings = embed_texts(vehicle_texts, batch_size=32, show_progress_bar=True)
    except Exception as exc:
        print(f"[WARN] Embedding generation failed: {exc}")
        embeddings = []

    db = SessionLocal()
    try:
        Base.metadata.create_all(bind=engine)
        ensure_runtime_schema()

        print("Clearing existing data...")
        db.query(ChatFeedback).delete()
        db.query(ChatSession).update({ChatSession.last_vehicle_id: None})
        db.commit()
        db.query(Vehicle).delete()
        db.commit()

        for inserted, payload in enumerate(prepared_rows, start=1):
            core_data = payload["core_data"]
            extra_info = payload["extra_info"]
            embedding = embeddings[inserted - 1] if inserted - 1 < len(embeddings) else None

            vehicle = Vehicle(
                **{
                    key: value
                    for key, value in core_data.items()
                    if hasattr(Vehicle, key) and value is not None
                },
                extra_info=extra_info or None,
                embedding=embedding,
            )
            db.add(vehicle)

            if inserted % 10 == 0:
                print(f"  ... {inserted} inserted so far")

        db.commit()

        faiss_ready = False
        if refresh_rag_artifacts:
            faiss_ready = build_rag_artifacts(documents, embeddings or None)
            try:
                from services.ev_rag import ev_rag_service

                ev_rag_service.reload()
                ev_rag_service.warmup()
            except Exception as exc:
                print(f"[WARN] Failed to refresh in-memory RAG artifacts: {exc}")

        inserted_count = len(prepared_rows)
        state = {
            "dataset_name": data_path.name,
            "dataset_signature": get_dataset_signature(data_path),
            "inserted": inserted_count,
            "skipped": skipped,
            "faiss_ready": faiss_ready,
            "rag_documents": len(documents),
            "imported_at": datetime.now(timezone.utc).isoformat(),
        }
        write_import_state(state)

        print(f"\n[SUCCESS] Import complete - Inserted: {inserted_count} | Skipped: {skipped}")
        return {"success": True, **state}

    except Exception as exc:
        db.rollback()
        import traceback

        print(f"[ERROR] {exc}")
        traceback.print_exc()
        return {"success": False, "message": str(exc)}
    finally:
        db.close()


if __name__ == "__main__":
    run_import()
