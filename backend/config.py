"""
config.py — Central configuration for DreamScape.
All modules import from here. Never read os.getenv() directly.
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    # ── LLM Providers ────────────────────────────────────────────────
    groq_api_key:       str  = Field("", env="GROQ_API_KEY")
    groq_model:         str  = Field("llama-3.1-8b-instant", env="GROQ_MODEL")
    cerebras_api_key:   str  = Field("", env="CEREBRAS_API_KEY")
    openrouter_api_key: str  = Field("", env="OPENROUTER_API_KEY")
    gemini_api_key:     str  = Field("", env="GEMINI_API_KEY")
    ollama_enabled:     bool = Field(False, env="OLLAMA_ENABLED")
    ollama_host:        str  = Field("http://localhost:11434", env="OLLAMA_HOST")

    # ── Image Generation ──────────────────────────────────────────────
    fal_api_key:         str = Field("", env="FAL_API_KEY")    # fal.ai (recommended)
    hf_api_token:        str = Field("", env="HF_API_TOKEN")   # HuggingFace fallback

    # ── Video Generation ──────────────────────────────────────────────
    magic_hour_api_key: str = Field("", env="MAGIC_HOUR_API_KEY")
    seedance_api_key:   str = Field("", env="SEEDANCE_API_KEY")

    # ── Storage ───────────────────────────────────────────────────────
    storage_base:        str = Field("./storage", env="STORAGE_BASE")
    chroma_persist_dir:  str = Field("./storage/chroma", env="CHROMA_PERSIST_DIR")

    # ── Database ──────────────────────────────────────────────────────
    database_url:        str = Field("sqlite:///./dreamscape.db", env="DATABASE_URL")

    # ── Video Generation ─────────────────────────────────
    cdance_api_key:    str = Field("", env="CDANCE_API_KEY")
    imgbb_api_key:     str = Field("", env="IMGBB_API_KEY")

    # ── App ───────────────────────────────────────────────────────────
    app_env:   str = Field("development", env="APP_ENV")
    log_level: str = Field("INFO", env="LOG_LEVEL")

    class Config:
        env_file          = ".env"
        env_file_encoding = "utf-8"
        extra             = "ignore"   # ignore unknown env vars silently


@lru_cache()
def get_settings() -> Settings:
    return Settings()
