from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    PROJECT_NAME: str = "EquityPulse"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str
    GOOGLE_API_KEY: str
    GEMINI_MODEL_NAME: str = "gemini-1.5-pro"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

@lru_cache
def get_settings() -> Settings:
    return Settings()
