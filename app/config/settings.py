from pydantic_settings import BaseSettings
from pydantic import Field, Extra
from typing import Optional
import os
from pathlib import Path
from urllib.parse import quote_plus


class DatabaseSettings(BaseSettings):
    """Database connection settings"""
    DB_TYPE: str = Field(...,
                         env="DB_TYPE")  # postgres, mongodb, mysql, sqlite
    DB_HOST: Optional[str] = Field(None, env="DB_HOST")
    DB_PORT: Optional[int] = Field(None, env="DB_PORT")
    DB_USER: Optional[str] = Field(None, env="DB_USER")
    DB_PASSWORD: Optional[str] = Field(None, env="DB_PASSWORD")
    DB_NAME: Optional[str] = Field(None, env="DB_NAME")
    DB_PATH: Optional[str] = Field(None, env="DB_PATH")  # For SQLite

    # MongoDB specific
    MONGO_AUTH_SOURCE: Optional[str] = Field("admin", env="MONGO_AUTH_SOURCE")

    # PostgreSQL specific
    POSTGRES_SCHEMA: Optional[str] = Field("public", env="POSTGRES_SCHEMA")

    # MySQL specific
    MYSQL_CHARSET: Optional[str] = Field("utf8mb4", env="MYSQL_CHARSET")

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = Extra.allow  # <-- Add this line


class APISettings(BaseSettings):
    """API and LLM settings"""
    # ANTHROPIC_API_KEY: str = Field(..., env="ANTHROPIC_API_KEY")
    API_HOST: str = Field("0.0.0.0", env="API_HOST")
    API_PORT: int = Field(8000, env="API_PORT")
    DEBUG: bool = Field(False, env="DEBUG")

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = Extra.allow  # <-- Add this line


# Create settings instances
db_settings = DatabaseSettings()
api_settings = APISettings()


def get_db_url() -> str:
    """Generate database URL based on type and settings"""
    if db_settings.DB_TYPE == "sqlite":
        return f"sqlite:///{db_settings.DB_PATH}"
    elif db_settings.DB_TYPE == "postgres":
        user = quote_plus(db_settings.DB_USER)
        password = quote_plus(db_settings.DB_PASSWORD)
        return f"postgresql://{user}:{password}@{db_settings.DB_HOST}:{db_settings.DB_PORT}/{db_settings.DB_NAME}"
    elif db_settings.DB_TYPE == "mysql":
        return f"mysql://{db_settings.DB_USER}:{db_settings.DB_PASSWORD}@{db_settings.DB_HOST}:{db_settings.DB_PORT}/{db_settings.DB_NAME}?charset={db_settings.MYSQL_CHARSET}"
    elif db_settings.DB_TYPE == "mongodb":
        auth = f"{db_settings.DB_USER}:{db_settings.DB_PASSWORD}@" if db_settings.DB_USER else ""
        return f"mongodb://{auth}{db_settings.DB_HOST}:{db_settings.DB_PORT}/{db_settings.DB_NAME}?authSource={db_settings.MONGO_AUTH_SOURCE}"
    else:
        raise ValueError(f"Unsupported database type: {db_settings.DB_TYPE}")
