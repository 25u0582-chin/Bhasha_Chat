from __future__ import annotations

import socketio

from app.domain import MessageSendRequest
from app.services.messages import MessageService


def build_socket_server(message_service: MessageService, redis_url: str | None = None) -> socketio.AsyncServer:
    manager = socketio.AsyncRedisManager(redis_url) if redis_url else None
    sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*", client_manager=manager)

    @sio.event
    async def connect(sid: str, environ: dict, auth: dict | None):  # type: ignore[override]
        user_id = (auth or {}).get("user_id")
        if user_id:
            await sio.enter_room(sid, user_id)

    @sio.event
    async def join(sid: str, data: dict):  # type: ignore[override]
        user_id = data.get("user_id")
        if user_id:
            await sio.enter_room(sid, user_id)
            await sio.emit("room:joined", {"user_id": user_id}, to=sid)

    @sio.event
    async def message_send(sid: str, data: dict):  # type: ignore[override]
        request = MessageSendRequest.model_validate(data)
        message = await message_service.send_message(request)
        payload = message.model_dump(mode="json")
        for recipient_id in request.recipient_ids:
            await sio.emit("message:delivered", payload, room=recipient_id)
        await sio.emit("message:ack", payload, to=sid)

    return sio


def build_asgi_app(api_app, socket_server: socketio.AsyncServer):
    return socketio.ASGIApp(socket_server, other_asgi_app=api_app)
