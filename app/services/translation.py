from __future__ import annotations

import asyncio
import httpx

from typing import Protocol


class TranslationProvider(Protocol):
    async def translate(self, text: str, source_language: str, target_language: str) -> str:
        raise NotImplementedError


class MockTranslationProvider:
    async def translate(self, text: str, source_language: str, target_language: str) -> str:
        if source_language == target_language:
            return text
        return f"[{target_language}] {text}"


class HttpTranslationProvider:
    def __init__(self, api_url: str, api_key: str | None = None) -> None:
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key

    async def translate(self, text: str, source_language: str, target_language: str) -> str:
        payload = {
            "text": text,
            "source_language": source_language,
            "target_language": target_language,
        }
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(f"{self.api_url}/translate", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data["translated_text"]


class GoogleTranslationProvider:
    def __init__(self) -> None:
        try:
            from deep_translator import GoogleTranslator  # noqa: F401
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("deep-translator is not installed") from exc

    async def translate(self, text: str, source_language: str, target_language: str) -> str:
        if source_language == target_language:
            return text

        from deep_translator import GoogleTranslator

        def _translate() -> str:
            translator = GoogleTranslator(source=source_language, target=target_language)
            return translator.translate(text)

        return await asyncio.to_thread(_translate)


def build_translation_provider(backend: str, api_url: str | None, api_key: str | None) -> TranslationProvider:
    if backend == "google":
        try:
            return GoogleTranslationProvider()
        except RuntimeError:
            return MockTranslationProvider()
    if backend == "http" and api_url:
        return HttpTranslationProvider(api_url=api_url, api_key=api_key)
    return MockTranslationProvider()
