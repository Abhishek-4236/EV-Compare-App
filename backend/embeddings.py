from functools import lru_cache
from sentence_transformers import SentenceTransformer

MODEL_NAME = "BAAI/bge-small-en-v1.5"
EMBEDDING_DIM = 384


@lru_cache(maxsize=1)
def get_model() -> SentenceTransformer:
    return SentenceTransformer(MODEL_NAME)


def embed_text(text: str) -> list[float]:
    model = get_model()
    vector = model.encode([text], normalize_embeddings=True)[0]
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

