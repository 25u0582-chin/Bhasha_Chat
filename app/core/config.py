from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


SCHEDULED_INDIAN_LANGUAGES: list[str] = [
    "as",
    "bn",
    "brx",
    "doi",
    "gu",
    "hi",
    "kn",
    "ks",
    "kok",
    "mai",
    "ml",
    "mni",
    "mr",
    "ne",
    "or",
    "pa",
    "sa",
    "sat",
    "sd",
    "ta",
    "te",
    "ur",
]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Multilingual Real-Time Chat Platform"
    environment: str = "development"
    redis_url: str | None = None
    postgres_url: str | None = None
    mongo_url: str | None = None
    translation_backend: str = "google"
    translation_api_url: str | None = None
    translation_api_key: str | None = None
    language_detector_backend: str = "heuristic"
    supported_languages: list[str] = Field(default_factory=lambda: SCHEDULED_INDIAN_LANGUAGES.copy())


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
