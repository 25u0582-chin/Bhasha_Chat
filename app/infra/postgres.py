from __future__ import annotations

from collections.abc import Iterable

from app.domain import UserPreferences
from app.storage import PreferenceRepository


class PostgresPreferenceRepository(PreferenceRepository):
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
        self._store: dict[str, UserPreferences] = {}

    async def upsert(self, preferences: UserPreferences) -> UserPreferences:
        self._store[preferences.user_id] = preferences
        return preferences

    async def get_many(self, user_ids: Iterable[str]) -> dict[str, UserPreferences]:
        return {user_id: self._store[user_id] for user_id in user_ids if user_id in self._store}
