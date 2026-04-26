from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class UserPreferences(BaseModel):
    user_id: str
    preferred_languages: list[str] = Field(default_factory=list)
    primary_language: str | None = None
    updated_at: datetime = Field(default_factory=utc_now)

    def resolved_primary_language(self) -> str:
        if self.primary_language:
            return self.primary_language
        if self.preferred_languages:
            return self.preferred_languages[0]
        return "en"


class PreferenceUpdateRequest(BaseModel):
    preferred_languages: list[str]
    primary_language: str | None = None


class PreferenceResponse(BaseModel):
    user_id: str
    preferred_languages: list[str]
    primary_language: str
    updated_at: datetime


class MessageAttachment(BaseModel):
    name: str
    mime_type: str
    data_url: str
    size_bytes: int | None = None


class MessageSendRequest(BaseModel):
    sender_id: str
    conversation_id: str
    text: str
    recipient_ids: list[str]
    source_language: str | None = None
    attachments: list[MessageAttachment] = Field(default_factory=list)


class TranslatedVariant(BaseModel):
    recipient_id: str
    target_language: str
    translated_text: str
    cache_hit: bool = False


class ChatMessage(BaseModel):
    message_id: str = Field(default_factory=lambda: uuid4().hex)
    conversation_id: str
    sender_id: str
    original_text: str
    source_language: str
    attachments: list[MessageAttachment] = Field(default_factory=list)
    translated_variants: list[TranslatedVariant] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
