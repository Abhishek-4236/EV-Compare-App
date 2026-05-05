from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List

BASE_DIR = Path(__file__).resolve().parents[1]
ENV_FILE = BASE_DIR / ".env"
PROJECT_ROOT = BASE_DIR.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "India EV Compare API"
    APP_ENV: str = "development"
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/ev_compare"
    
    # JWT Auth
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # AI providers
    GEMINI_API_KEY: str | None = None
    OPENAI_ENABLED: bool = False
    OPENAI_API_KEY: str | None = None
    OPENAI_CHAT_MODEL: str = "gpt-4o-mini"
    OPENAI_QUERY_PARSER_MODEL: str = "gpt-4o-mini"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_EMBEDDING_DIMENSIONS: int = 1536
    OPENAI_TIMEOUT_SECONDS: int = 30
    GROQ_API_KEY: str | None = None
    GROQ_MODEL: str = "meta-llama/Llama-3.1-8B-Instruct:novita"
    GROQ_MODEL_ENABLED: bool = True
    HF_API_KEY: str | None = None
    HF_MODEL: str = "katanemo/Arch-Router-1.5B:hf-inference"
    HF_MODEL_ENABLED: bool = True
    LLM_TIMEOUT_SECONDS: int = 8
    RAG_TOP_K: int = 3
    NVIDIA_API_KEY: str | None = None
    NVIDIA_API_BASE: str = "https://integrate.api.nvidia.com"
    NVIDIA_RERANK_URL: str = "https://ai.api.nvidia.com/v1/retrieval/nvidia/llama-3_2-nv-rerankqa-1b-v2/reranking"
    NVIDIA_RERANK_ENABLED: bool = False
    NVIDIA_RERANK_MODEL: str = "nvidia/llama-3.2-nv-rerankqa-1b-v2"
    NVIDIA_RERANK_TIMEOUT_SECONDS: int = 6
    NVIDIA_RERANK_MAX_CANDIDATES: int = 20

    @field_validator(
        "OPENAI_ENABLED",
        "GROQ_MODEL_ENABLED",
        "HF_MODEL_ENABLED",
        "NVIDIA_RERANK_ENABLED",
        "AUTO_IMPORT_DATA_ON_STARTUP",
        "AUTO_OPEN_BROWSER",
        mode="before",
    )
    @classmethod
    def parse_lenient_bool(cls, value):
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized == "":
                return False
            if normalized in {"tr", "tru"}:
                return True
        return value

    # Local startup helpers
    AUTO_IMPORT_DATA_ON_STARTUP: bool = True
    AUTO_OPEN_BROWSER: bool = True
    APP_OPEN_URL: str | None = "http://127.0.0.1:8000/docs"

    # EV chatbot artifacts
    EV_EXCEL_PATH: str = str(PROJECT_ROOT / "data" / "raw" / "India_EV_All_Segments_Dataset_2026_filled.xlsx")
    EV_JSON_PATH: str = str(BASE_DIR / "data" / "processed" / "vehicles.json")
    EV_FAISS_INDEX_PATH: str = str(BASE_DIR / "data" / "processed" / "vehicles.faiss")
    EV_FAISS_META_PATH: str = str(BASE_DIR / "data" / "processed" / "vehicles.meta.json")

    @field_validator("EV_EXCEL_PATH", "EV_JSON_PATH", "EV_FAISS_INDEX_PATH", "EV_FAISS_META_PATH")
    @classmethod
    def resolve_project_path(cls, value: str) -> str:
        path = Path(value)
        if path.is_absolute():
            return str(path)
        return str(PROJECT_ROOT / path)

    # CORS Origins
    FRONTEND_URL: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    model_config = SettingsConfigDict(env_file=ENV_FILE, env_file_encoding="utf-8", extra="ignore")

settings = Settings()
