import socketio

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")


async def emit_slide_changed(room_id: str, slide_index: int) -> None:
    await sio.emit("slide_changed", {"room_id": room_id, "slide_index": slide_index}, room=room_id)


async def emit_presentation_ended(room_id: str) -> None:
    await sio.emit("presentation_ended", {"room_id": room_id}, room=room_id)


async def emit_reaction(room_id: str, emoji_type: str) -> None:
    await sio.emit("reaction", {"room_id": room_id, "emoji_type": emoji_type}, room=room_id)


@sio.event
async def join_room(sid: str, data: dict) -> None:
    room_id = data["room_id"]
    await sio.enter_room(sid, room_id)


@sio.event
async def leave_room(sid: str, data: dict) -> None:
    room_id = data["room_id"]
    await sio.leave_room(sid, room_id)
