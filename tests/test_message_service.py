from __future__ import annotations

import pytest

from app.domain import MessageSendRequest, UserPreferences
from app.services.detection import HeuristicLanguageDetector
from app.services.messages import MessageService
from app.services.translation import MockTranslationProvider
from app.storage import InMemoryMessageRepository, InMemoryPreferenceCache, InMemoryPreferenceRepository, InMemoryTranslationCache


@pytest.mark.asyncio
async def test_send_message_uses_single_preference_cache_hit_and_translates_per_recipient() -> None:
    preference_repository = InMemoryPreferenceRepository()
    preference_cache = InMemoryPreferenceCache()
    message_repository = InMemoryMessageRepository()
    translation_cache = InMemoryTranslationCache()
    translation_provider = MockTranslationProvider()
    language_detector = HeuristicLanguageDetector()

    service = MessageService(
        preference_repository=preference_repository,
        preference_cache=preference_cache,
        message_repository=message_repository,
        translation_cache=translation_cache,
        translation_provider=translation_provider,
        language_detector=language_detector,
        supported_languages=["hi", "ta", "en"],
    )

    await service.upsert_preferences(
        "sender",
        UserPreferences(user_id="sender", preferred_languages=["hi"]),
    )
    await service.upsert_preferences(
        "recipient-1",
        UserPreferences(user_id="recipient-1", preferred_languages=["ta"]),
    )

    message = await service.send_message(
        MessageSendRequest(
            sender_id="sender",
            conversation_id="conversation-1",
            text="hello there",
            recipient_ids=["recipient-1"],
            source_language="en",
        )
    )

    assert preference_cache.mget_call_count == 1
    assert len(message.translated_variants) == 1
    assert message.translated_variants[0].recipient_id == "recipient-1"
    assert message.translated_variants[0].target_language == "ta"
    assert message.translated_variants[0].translated_text == "[ta] hello there"
    assert len(message_repository.messages) == 1
