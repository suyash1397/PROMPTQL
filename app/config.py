from pydantic import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    DATABASE_URL: str
    MONGO_URL: str
    ANTHROPIC_API_KEY: str

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings() 