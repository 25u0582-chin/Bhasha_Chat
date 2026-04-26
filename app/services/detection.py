from __future__ import annotations

from typing import Protocol


class LanguageDetector(Protocol):
    async def detect(self, text: str, fallback: str = "en") -> str:
        raise NotImplementedError


class HeuristicLanguageDetector:
    devanagari_sample = {"है", "और", "नहीं", "किया", "क्या"}
    tamil_sample = {"இ", "அ", "ஆ", "எ", "ஏ", "தமிழ்"}
    telugu_sample = {"అ", "ఆ", "ఇ", "ఉ", "తెలుగు"}
    urdu_sample = {"ہے", "اور", "نہیں", "کیا"}
    bengali_sample = {"আমি", "এবং", "না", "কি"}

    async def detect(self, text: str, fallback: str = "en") -> str:
        if any(character in text for character in self.tamil_sample):
            return "ta"
        if any(character in text for character in self.telugu_sample):
            return "te"
        if any(character in text for character in self.urdu_sample):
            return "ur"
        if any(character in text for character in self.bengali_sample):
            return "bn"
        if any(character in text for character in self.devanagari_sample) or any(
            "\u0900" <= character <= "\u097F" for character in text
        ):
            return "hi"
        lowered_text = text.lower()
        if any(marker in lowered_text for marker in ("yaar", "bhai", "kya", "nahi", "hain")):
            return "hi"
        if any(marker in lowered_text for marker in ("la", "da", "illa", "enna")):
            return "ta"
        return fallback


class LinguaLanguageDetector:
    def __init__(self) -> None:
        try:
            from lingua import Language, LanguageDetectorBuilder
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("lingua-language-detector is not installed") from exc

        languages = [
            Language.ENGLISH,
            Language.HINDI,
            Language.BENGALI,
            Language.TAMIL,
            Language.TELUGU,
            Language.MARATHI,
            Language.GUJARATI,
            Language.PUNJABI,
            Language.URDU,
            Language.MALAYALAM,
            Language.KANNADA,
            Language.ODIA,
            Language.ASSAMESE,
        ]
        self._language_map = {
            Language.ENGLISH: "en",
            Language.HINDI: "hi",
            Language.BENGALI: "bn",
            Language.TAMIL: "ta",
            Language.TELUGU: "te",
            Language.MARATHI: "mr",
            Language.GUJARATI: "gu",
            Language.PUNJABI: "pa",
            Language.URDU: "ur",
            Language.MALAYALAM: "ml",
            Language.KANNADA: "kn",
            Language.ODIA: "or",
            Language.ASSAMESE: "as",
        }
        self._detector = LanguageDetectorBuilder.from_languages(*languages).build()

    async def detect(self, text: str, fallback: str = "en") -> str:
        detected_language = self._detector.detect_language_of(text)
        if detected_language is None:
            return fallback
        return self._language_map.get(detected_language, fallback)
