from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    env: Literal["development", "production", "test"] = "development"
    app_name: str = "Product Review API"
    debug: bool = True

    # Auth
    auth_provider: Literal["local", "supabase"] = "local"
    jwt_secret: str = "change-me-in-production-use-long-random-string"
    jwt_algorithm: str = "HS256"
    jwt_access_expire_min: int = 15
    jwt_refresh_expire_days: int = 30

    # Supabase
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    supabase_jwt_secret: str = ""

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/product_review"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Pipeline — tiered Groq models: fast 8B for parse/report, 70B for regulatory enrichment
    pipeline_phase: Literal["build", "local"] = "build"
    model_stage0: str = "openfoodfacts/spellcheck-mistral-7b"
    model_stage1: str = "llama-3.1-8b-instant"
    model_stage2_assist: str = "foodyllm"
    model_stage2: str = "llama-3.3-70b-versatile"
    model_stage3: str = "llama-3.1-8b-instant"

    # Providers — Groq + Tavily + Tesseract only (no paid fallbacks by default)
    provider_llm: str = "groq"
    provider_llm_fallback: str = ""
    provider_llm_stage0: str = "ollama"
    provider_llm_stage2_assist: str = "huggingface_local"
    provider_ocr: str = "tesseract"
    provider_ocr_fallback: str = ""
    provider_search: str = "tavily"
    provider_search_fallback: str = ""
    provider_storage: Literal["local", "supabase"] = "local"

    # Tavily budget per scan (Stage 3 searches flagged ingredients only)
    search_max_queries: int = 5
    search_max_results_per_query: int = 2

    # External API keys
    ollama_base_url: str = "http://localhost:11434"
    groq_api_key: str = ""
    together_api_key: str = ""
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    tavily_api_key: str = ""
    google_vision_credentials: str = ""

    # Rate limiting
    rate_limit_per_minute: int = 60

    # Storage
    local_storage_path: str = "./storage"

    # Regulatory search domains
    search_domains: list[str] = [
        "efsa.europa.eu",
        "pubmed.ncbi.nlm.nih.gov",
        "fda.gov",
        "who.int",
        "fssai.gov.in",
    ]

    disclaimer: str = "Informational only. Not medical advice."


@lru_cache
def get_settings() -> Settings:
    return Settings()
