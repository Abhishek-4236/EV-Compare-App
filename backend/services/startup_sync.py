from __future__ import annotations

import json
import tempfile
import time
import webbrowser
from pathlib import Path
from threading import Thread

from database import SessionLocal
from models import Vehicle
from scripts.import_excel import (
    get_dataset_signature,
    get_preferred_dataset_path,
    read_import_state,
    run_import,
)
from services.embeddings import start_model_warmup
from services.ev_rag import ev_rag_service

from core.config import settings

BROWSER_LOCK_PATH = Path(tempfile.gettempdir()) / "ev_compare_browser_lock.json"


def get_vehicle_count() -> int | None:
    db = SessionLocal()
    try:
        return db.query(Vehicle).count()
    except Exception:
        return None
    finally:
        db.close()


def ensure_data_ready_on_startup() -> dict:
    dataset_path = get_preferred_dataset_path()
    if not settings.AUTO_IMPORT_DATA_ON_STARTUP or dataset_path is None:
        start_model_warmup()
        ev_rag_service.reload()
        ev_rag_service.warmup()
        return {
            "success": True,
            "imported": False,
            "dataset_name": dataset_path.name if dataset_path else None,
        }

    import_state = read_import_state()
    vehicle_count = get_vehicle_count()
    dataset_signature = get_dataset_signature(dataset_path)
    expected_count = import_state.get("inserted") if import_state else None

    needs_import = (
        import_state is None
        or import_state.get("dataset_signature") != dataset_signature
        or vehicle_count in {None, 0}
        or (expected_count is not None and vehicle_count != expected_count)
    )

    if needs_import:
        result = run_import(dataset_path=dataset_path, refresh_rag_artifacts=True)
        result["imported"] = bool(result.get("success"))
        return result

    start_model_warmup()
    ev_rag_service.reload()
    ev_rag_service.warmup()
    return {
        "success": True,
        "imported": False,
        "dataset_name": dataset_path.name,
        "inserted": vehicle_count,
        "skipped": import_state.get("skipped", 0),
        "faiss_ready": import_state.get("faiss_ready", False),
    }


def maybe_open_startup_url() -> str | None:
    if not settings.AUTO_OPEN_BROWSER or settings.APP_ENV.lower() != "development":
        return None

    url = settings.APP_OPEN_URL or "http://127.0.0.1:8000/docs"
    now = time.time()
    if BROWSER_LOCK_PATH.exists():
        try:
            payload = json.loads(BROWSER_LOCK_PATH.read_text(encoding="utf-8"))
            if payload.get("url") == url and (now - float(payload.get("timestamp", 0))) < 10:
                return None
        except Exception:
            pass

    try:
        BROWSER_LOCK_PATH.write_text(
            json.dumps({"url": url, "timestamp": now}),
            encoding="utf-8",
        )
    except Exception:
        return None

    Thread(target=lambda: webbrowser.open(url, new=2), daemon=True).start()
    return url
