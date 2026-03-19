from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    supabase_url: str = Field(..., alias="SUPABASE_URL")
    supabase_key: str = Field(..., alias="SUPABASE_KEY")
    groq_api_key: str = Field(..., alias="GROQ_API_KEY")
    groq_model: str = Field("llama-3.3-70b-versatile", alias="GROQ_MODEL")
    groq_base_url: str = Field("https://api.groq.com/openai/v1", alias="GROQ_BASE_URL")
    llm_timeout_seconds: float = Field(15.0, alias="LLM_TIMEOUT_SECONDS")
    app_name: str = "IAtria Lead Triage"
    app_env: str = "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
