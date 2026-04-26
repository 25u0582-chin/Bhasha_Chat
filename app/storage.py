from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

from app.domain import ChatMessage, UserPreferences


class PreferenceRepository(Protocol):
    async def upsert(self, preferences: UserPreferences) -> UserPreferences:
        raise NotImplementedError

    async def get_many(self, user_ids: Iterable[str]) -> dict[str, UserPreferences]:
        raise NotImplementedError


class MessageRepository(Protocol):
    async def store(self, message: ChatMessage) -> ChatMessage:
        raise NotImplementedError


class PreferenceCache(Protocol):
    async def mget(self, user_ids: Iterable[str]) -> dict[str, UserPreferences]:
        raise NotImplementedError

    async def set_many(self, preferences: dict[str, UserPreferences]) -> None:
        raise NotImplementedError


class TranslationCache(Protocol):
    async def get(self, cache_key: str) -> str | None:
        raise NotImplementedError

    async def set(self, cache_key: str, translated_text: str) -> None:
        raise NotImplementedError


class InMemoryPreferenceRepository:
    def __init__(self) -> None:
        self._store: dict[str, UserPreferences] = {}

    async def upsert(self, preferences: UserPreferences) -> UserPreferences:
        self._store[preferences.user_id] = preferences
        return preferences

    async def get_many(self, user_ids: Iterable[str]) -> dict[str, UserPreferences]:
        return {user_id: self._store[user_id] for user_id in user_ids if user_id in self._store}


class InMemoryMessageRepository:
    def __init__(self) -> None:
        self.messages: list[ChatMessage] = []

    async def store(self, message: ChatMessage) -> ChatMessage:
        self.messages.append(message)
        return message


class InMemoryPreferenceCache:
    def __init__(self) -> None:
        self._store: dict[str, str] = {}
        self.mget_call_count = 0

    async def mget(self, user_ids: Iterable[str]) -> dict[str, UserPreferences]:
        self.mget_call_count += 1
        result: dict[str, UserPreferences] = {}
        for user_id in user_ids:
            raw_value = self._store.get(user_id)
            if raw_value is not None:
                result[user_id] = UserPreferences.model_validate_json(raw_value)
        return result

    async def set_many(self, preferences: dict[str, UserPreferences]) -> None:
        for user_id, preference in preferences.items():
            self._store[user_id] = preference.model_dump_json()


class InMemoryTranslationCache:
    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    async def get(self, cache_key: str) -> str | None:
        return self._store.get(cache_key)

    async def set(self, cache_key: str, translated_text: str) -> None:
        self._store[cache_key] = translated_text


class RedisPreferenceCache:
    def __init__(self, client: object) -> None:
        self._client = client

    async def mget(self, user_ids: Iterable[str]) -> dict[str, UserPreferences]:
        user_id_list = list(user_ids)
        raw_values = await self._client.mget(*user_id_list)
        result: dict[str, UserPreferences] = {}
        for user_id, raw_value in zip(user_id_list, raw_values, strict=False):
            if raw_value is None:
                continue
            decoded = raw_value.decode("utf-8") if isinstance(raw_value, bytes) else raw_value
            result[user_id] = UserPreferences.model_validate_json(decoded)
        return result

    async def set_many(self, preferences: dict[str, UserPreferences]) -> None:
        payload = {user_id: preference.model_dump_json() for user_id, preference in preferences.items()}
        if payload:
            await self._client.mset(payload)


class RedisTranslationCache:
    def __init__(self, client: object, prefix: str = "translation-cache") -> None:
        self._client = client
        self._prefix = prefix

    def _key(self, cache_key: str) -> str:
        return f"{self._prefix}:{cache_key}"

    async def get(self, cache_key: str) -> str | None:
        raw_value = await self._client.get(self._key(cache_key))
        if raw_value is None:
            return None
        return raw_value.decode("utf-8") if isinstance(raw_value, bytes) else raw_value

    async def set(self, cache_key: str, translated_text: str) -> None:
        await self._client.set(self._key(cache_key), translated_text)
