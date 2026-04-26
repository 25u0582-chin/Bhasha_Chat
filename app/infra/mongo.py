from __future__ import annotations

from collections.abc import Iterable

from app.domain import ChatMessage
from app.storage import MessageRepository


class MongoMessageRepository(MessageRepository):
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
        self.messages: list[ChatMessage] = []

    async def store(self, message: ChatMessage) -> ChatMessage:
        self.messages.append(message)
        return message
