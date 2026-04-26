from __future__ import annotations

from app.core.config import Settings
from app.storage import (
    InMemoryMessageRepository,
    InMemoryPreferenceCache,
    InMemoryPreferenceRepository,
    InMemoryTranslationCache,
    MessageRepository,
    PreferenceCache,
    PreferenceRepository,
    TranslationCache,
)


def build_preference_repository(settings: Settings) -> PreferenceRepository:
    if settings.postgres_url:
        from app.infra.postgres import PostgresPreferenceRepository

        return PostgresPreferenceRepository(settings.postgres_url)
    return InMemoryPreferenceRepository()


def build_message_repository(settings: Settings) -> MessageRepository:
    if settings.mongo_url:
        from app.infra.mongo import MongoMessageRepository

        return MongoMessageRepository(settings.mongo_url)
    return InMemoryMessageRepository()


def build_preference_cache(settings: Settings) -> PreferenceCache:
    if settings.redis_url:
        from app.infra.redis import RedisClientFactory, RedisPreferenceCache

        client = RedisClientFactory.from_url(settings.redis_url)
        return RedisPreferenceCache(client)
    return InMemoryPreferenceCache()


def build_translation_cache(settings: Settings) -> TranslationCache:
    if settings.redis_url:
        from app.infra.redis import RedisClientFactory, RedisTranslationCache

        client = RedisClientFactory.from_url(settings.redis_url)
        return RedisTranslationCache(client)
    return InMemoryTranslationCache()
