from __future__ import annotations

import hashlib

from app.core.languages import is_supported_language
from app.domain import ChatMessage, MessageSendRequest, PreferenceResponse, TranslatedVariant, UserPreferences
from app.services.detection import LanguageDetector
from app.services.translation import TranslationProvider
from app.storage import MessageRepository, PreferenceCache, PreferenceRepository, TranslationCache


class MessageService:
    def __init__(
        self,
        preference_repository: PreferenceRepository,
        preference_cache: PreferenceCache,
        message_repository: MessageRepository,
        translation_cache: TranslationCache,
        translation_provider: TranslationProvider,
        language_detector: LanguageDetector,
        supported_languages: list[str],
    ) -> None:
        self.preference_repository = preference_repository
        self.preference_cache = preference_cache
        self.message_repository = message_repository
        self.translation_cache = translation_cache
        self.translation_provider = translation_provider
        self.language_detector = language_detector
        self.supported_languages = supported_languages

    async def upsert_preferences(self, user_id: str, preferences: UserPreferences) -> PreferenceResponse:
        stored_preferences = await self.preference_repository.upsert(
            preferences.model_copy(update={"user_id": user_id})
        )
        await self.preference_cache.set_many({user_id: stored_preferences})
        return PreferenceResponse(
            user_id=stored_preferences.user_id,
            preferred_languages=stored_preferences.preferred_languages,
            primary_language=stored_preferences.resolved_primary_language(),
            updated_at=stored_preferences.updated_at,
        )

    async def get_preferences(self, user_id: str) -> PreferenceResponse:
        cached_preferences = await self.preference_cache.mget([user_id])
        if user_id not in cached_preferences:
            fetched_preferences = await self.preference_repository.get_many([user_id])
            cached_preferences.update(fetched_preferences)
            if fetched_preferences:
                await self.preference_cache.set_many(fetched_preferences)

        preference = cached_preferences.get(user_id) or UserPreferences(user_id=user_id, preferred_languages=["en"])
        return PreferenceResponse(
            user_id=preference.user_id,
            preferred_languages=preference.preferred_languages,
            primary_language=preference.resolved_primary_language(),
            updated_at=preference.updated_at,
        )

    async def send_message(self, request: MessageSendRequest) -> ChatMessage:
        user_ids = [request.sender_id, *request.recipient_ids]
        cached_preferences = await self.preference_cache.mget(user_ids)

        missing_ids = [user_id for user_id in user_ids if user_id not in cached_preferences]
        if missing_ids:
            fetched_preferences = await self.preference_repository.get_many(missing_ids)
            cached_preferences.update(fetched_preferences)
            if fetched_preferences:
                await self.preference_cache.set_many(fetched_preferences)

        source_language = request.source_language or await self.language_detector.detect(request.text)
        original_text = request.text
        translated_variants: list[TranslatedVariant] = []

        for recipient_id in request.recipient_ids:
            recipient_preferences = cached_preferences.get(recipient_id) or UserPreferences(
                user_id=recipient_id,
                preferred_languages=[source_language],
            )
            target_language = self._select_target_language(recipient_preferences, source_language)
            translated_text, cache_hit = await self._translate_with_cache(
                original_text=original_text,
                source_language=source_language,
                target_language=target_language,
            )
            translated_variants.append(
                TranslatedVariant(
                    recipient_id=recipient_id,
                    target_language=target_language,
                    translated_text=translated_text,
                    cache_hit=cache_hit,
                )
            )

        message = ChatMessage(
            conversation_id=request.conversation_id,
            sender_id=request.sender_id,
            original_text=original_text,
            source_language=source_language,
            attachments=request.attachments,
            translated_variants=translated_variants,
        )
        return await self.message_repository.store(message)

    def _select_target_language(self, preference: UserPreferences, source_language: str) -> str:
        for candidate in preference.preferred_languages or [preference.resolved_primary_language()]:
            if candidate != source_language and is_supported_language(candidate, self.supported_languages):
                return candidate
        fallback_language = preference.resolved_primary_language()
        if is_supported_language(fallback_language, self.supported_languages):
            return fallback_language
        return "en"

    async def _translate_with_cache(
        self,
        original_text: str,
        source_language: str,
        target_language: str,
    ) -> tuple[str, bool]:
        cache_key = self._translation_cache_key(original_text, source_language, target_language)
        cached_translation = await self.translation_cache.get(cache_key)
        if cached_translation is not None:
            return cached_translation, True

        translated_text = await self.translation_provider.translate(original_text, source_language, target_language)
        await self.translation_cache.set(cache_key, translated_text)
        return translated_text, False

    @staticmethod
    def _translation_cache_key(original_text: str, source_language: str, target_language: str) -> str:
        digest = hashlib.sha256(original_text.encode("utf-8")).hexdigest()
        return f"{digest}:{source_language}:{target_language}"
