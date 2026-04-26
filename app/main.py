from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.domain import MessageSendRequest, PreferenceResponse, PreferenceUpdateRequest, UserPreferences
from app.infra.factory import (
    build_message_repository,
    build_preference_cache,
    build_preference_repository,
    build_translation_cache,
)
from app.realtime import build_asgi_app, build_socket_server
from app.services.detection import HeuristicLanguageDetector, LinguaLanguageDetector
from app.services.messages import MessageService
from app.services.translation import build_translation_provider
from app.storage import (
    InMemoryMessageRepository,
    InMemoryPreferenceCache,
    InMemoryPreferenceRepository,
    InMemoryTranslationCache,
)


settings = get_settings()
preference_repository = build_preference_repository(settings)
preference_cache = build_preference_cache(settings)
message_repository = build_message_repository(settings)
translation_cache = build_translation_cache(settings)
translation_provider = build_translation_provider(
    settings.translation_backend,
    settings.translation_api_url,
    settings.translation_api_key,
)

try:
    language_detector = LinguaLanguageDetector() if settings.language_detector_backend == "lingua" else HeuristicLanguageDetector()
except RuntimeError:
    language_detector = HeuristicLanguageDetector()

message_service = MessageService(
    preference_repository=preference_repository,
    preference_cache=preference_cache,
    message_repository=message_repository,
    translation_cache=translation_cache,
    translation_provider=translation_provider,
    language_detector=language_detector,
    supported_languages=settings.supported_languages,
)

fastapi_app = FastAPI(title=settings.app_name)
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
socket_server = build_socket_server(message_service, settings.redis_url)
app = build_asgi_app(fastapi_app, socket_server)


@fastapi_app.get("/health")
async def health() -> dict[str, str | int]:
    return {
        "status": "ok",
        "environment": settings.environment,
        "supported_languages": len(settings.supported_languages),
    }


@fastapi_app.put("/users/{user_id}/preferences", response_model=PreferenceResponse)
async def update_preferences(user_id: str, request: PreferenceUpdateRequest) -> PreferenceResponse:
    preferences = UserPreferences(
        user_id=user_id,
        preferred_languages=request.preferred_languages,
        primary_language=request.primary_language,
    )
    return await message_service.upsert_preferences(user_id, preferences)


@fastapi_app.get("/users/{user_id}/preferences", response_model=PreferenceResponse)
async def read_preferences(user_id: str) -> PreferenceResponse:
    return await message_service.get_preferences(user_id)


@fastapi_app.post("/messages")
async def send_message(request: MessageSendRequest) -> dict[str, object]:
    if not request.recipient_ids:
        raise HTTPException(status_code=400, detail="recipient_ids cannot be empty")
    message = await message_service.send_message(request)
    return message.model_dump(mode="json")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
