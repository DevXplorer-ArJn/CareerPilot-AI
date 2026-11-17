from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    tavily_api_key: str
    llm_api_key: str
    llm_base_url: str = "https://openrouter.ai/api/v1"
    llm_model: str = "meta-llama/llama-3.3-70b-instruct"
    database_url: str = "sqlite:///./careerpilot.db"
    jwt_secret: str = "change-this-secret-in-production"
    jwt_expiry_minutes: int = 60 * 24 * 7
    frontend_url: str = "http://localhost:3000"
    tavily_topic: str = "general"
    tavily_search_depth: str = "advanced"
    tavily_time_range: str = "month"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
