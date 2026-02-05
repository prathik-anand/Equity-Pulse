from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    PROJECT_NAME: str = "EquityPulse"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str
    GOOGLE_API_KEY: str
    GEMINI_MODEL_NAME: str = "gemini-1.5-pro"
    
    # Langfuse Integration
    LANGFUSE_PUBLIC_KEY: str | None = None
    LANGFUSE_SECRET_KEY: str | None = None
    LANGFUSE_HOST: str | None = None

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

@lru_cache
def get_settings() -> Settings:
    return Settings()
