from functools import lru_cache
from sentence_transformers import SentenceTransformer

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
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
