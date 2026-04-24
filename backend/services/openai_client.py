from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from pydantic import BaseModel, ValidationError

from core.config import settings


@lru_cache(maxsize=1)
def get_openai_client() -> Any:
    if not settings.OPENAI_ENABLED:
        raise RuntimeError("OpenAI services are disabled")
    if not settings.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not configured")
    from openai import OpenAI
    return OpenAI(api_key=settings.OPENAI_API_KEY, timeout=settings.OPENAI_TIMEOUT_SECONDS)


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    client = get_openai_client()
    response = client.embeddings.create(
        model=settings.OPENAI_EMBEDDING_MODEL,
        input=texts,
        dimensions=settings.OPENAI_EMBEDDING_DIMENSIONS,
    )
    return [item.embedding for item in response.data]


def parse_structured_output(
    *,
    model: str,
    system_prompt: str,
    user_prompt: str,
    schema_model: type[BaseModel],
) -> BaseModel:
    client = get_openai_client()
    response = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": schema_model.__name__,
                "strict": True,
                "schema": schema_model.model_json_schema(),
            }
        },
    )
    try:
        return schema_model.model_validate_json(response.output_text)
    except ValidationError:
        data = json.loads(response.output_text)
        return schema_model.model_validate(data)


def generate_text(
    *,
    system_prompt: str,
    user_prompt: str,
    model: str | None = None,
) -> str:
    client = get_openai_client()
    response = client.responses.create(
        model=model or settings.OPENAI_CHAT_MODEL,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return (response.output_text or "").strip()
