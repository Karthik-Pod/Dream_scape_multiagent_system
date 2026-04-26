"""
config.py — Central configuration using pydantic-settings.
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    # ── LLM ──────────────────────────────────────────────
    groq_api_key: str = Field(..., env="GROQ_API_KEY")
    groq_model:   str = Field("llama-3.1-8b-instant", env="GROQ_MODEL")

    # ── Database ──────────────────────────────────────────
    database_url: str = Field("sqlite:///./dreamscape.db", env="DATABASE_URL")

    # ── Vector Store ──────────────────────────────────────
    chroma_persist_dir: str = Field("./storage/chroma", env="CHROMA_PERSIST_DIR")

    # ── Storage ───────────────────────────────────────────
    storage_base: str = Field("./storage", env="STORAGE_BASE")

    # ── ComfyUI ───────────────────────────────────────────
    comfyui_url: str = Field("http://127.0.0.1:8188", env="COMFYUI_URL")

    # ── Multi-LLM Providers ──────────────────────────────
    gemini_api_key: str  = Field("", env="GEMINI_API_KEY")
    ollama_enabled: bool = Field(False, env="OLLAMA_ENABLED")
    ollama_host:    str  = Field("http://localhost:11434", env="OLLAMA_HOST")

    # ── HuggingFace (image generation) ───────────────────
    hf_api_token: str = Field("", env="HF_API_TOKEN")

    # ── Magic Hour (image-to-video) ───────────────────────
    magic_hour_api_key: str = Field("", env="MAGIC_HOUR_API_KEY")

    # ── Celery / Redis ────────────────────────────────────
    redis_url: str = Field("redis://localhost:6379/0", env="REDIS_URL")

    # ── App ───────────────────────────────────────────────
    app_env:   str = Field("development", env="APP_ENV")
    log_level: str = Field("INFO", env="LOG_LEVEL")

    class Config:
        env_file          = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
