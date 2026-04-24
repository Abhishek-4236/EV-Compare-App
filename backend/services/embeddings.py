from threading import Lock, Thread
from typing import Any

MODEL_NAME = "BAAI/bge-small-en-v1.5"
EMBEDDING_DIM = 384
_MODEL: Any | None = None
_MODEL_LOAD_ERROR: Exception | None = None
_MODEL_WARMING = False
_WARMUP_LOCK = Lock()


def get_model():
    global _MODEL, _MODEL_LOAD_ERROR
    if _MODEL is not None:
        return _MODEL
    if _MODEL_LOAD_ERROR is not None:
        raise RuntimeError("Embedding model is unavailable in this process") from _MODEL_LOAD_ERROR
    try:
        from sentence_transformers import SentenceTransformer
        _MODEL = SentenceTransformer(MODEL_NAME)
        return _MODEL
    except Exception as exc:
        _MODEL_LOAD_ERROR = exc
        raise


def is_model_ready() -> bool:
    return _MODEL is not None


def start_model_warmup() -> None:
    global _MODEL_WARMING
    with _WARMUP_LOCK:
        if _MODEL_WARMING or _MODEL_LOAD_ERROR is not None:
            return
        _MODEL_WARMING = True

    def _warmup():
        global _MODEL_WARMING
        try:
            get_model()
        except Exception:
            pass
        finally:
            _MODEL_WARMING = False

    Thread(target=_warmup, daemon=True).start()


def embed_text(text: str) -> list[float]:
    return embed_texts([text])[0]


def embed_texts(texts: list[str], batch_size: int = 32, show_progress_bar: bool = False) -> list[list[float]]:
    if not texts:
        return []
    model = get_model()
    vectors = model.encode(
        texts,
        batch_size=batch_size,
        normalize_embeddings=True,
        show_progress_bar=show_progress_bar,
    )
    return [vector.tolist() for vector in vectors]


def embed_text_if_ready(text: str) -> list[float] | None:
    if _MODEL is None or _MODEL_LOAD_ERROR is not None:
        return None
    vector = _MODEL.encode([text], normalize_embeddings=True)[0]
    return vector.tolist()


def vehicle_to_text(vehicle) -> str:
    parts = [
        f"{vehicle.brand} {vehicle.model}",
        f"category {vehicle.category}",
        f"wheel {vehicle.wheel_type}" if vehicle.wheel_type else None,
        f"price {vehicle.approx_price_inr}",
        f"range {vehicle.range_km} km",
        f"battery {vehicle.battery_kwh} kWh",
        f"top speed {vehicle.top_speed_kmh} kmph" if vehicle.top_speed_kmh else None,
        f"charging {vehicle.charging_type}" if vehicle.charging_type else None,
        f"subsidy {vehicle.fame2_subsidy_inr}" if vehicle.fame2_subsidy_inr else None,
        f"rating {vehicle.overall_rating}" if vehicle.overall_rating else None,
    ]
    return ". ".join([p for p in parts if p])


def chunk_text(text: str, max_chars: int = 1000) -> list[str]:
    """Naive splitter: splits long text into ~max_chars chunks at sentence boundaries."""
    paragraphs: list[str] = []
    current = []

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if sum(len(p) for p in current) + len(line) + 1 > max_chars:
            if current:
                paragraphs.append(" ".join(current))
                current = []
        current.append(line)

    if current:
        paragraphs.append(" ".join(current))

    return paragraphs
