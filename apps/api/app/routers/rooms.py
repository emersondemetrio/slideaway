import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from user_agents import parse as parse_user_agent

from app.database import get_db
from app.deps import get_current_user, owns_or_super_admin
from app.models import Deck, DeckSeries, Participant, Reaction, Room, RoomStatus, User
from app.schemas import CheckinRequest, CheckinResponse, ReactRequest, RoomOut
from app.sockets import emit_presentation_ended, emit_reaction, emit_slide_changed

router = APIRouter(tags=["rooms"])


async def _get_deck_or_404(db: AsyncSession, deck_id: uuid.UUID) -> Deck:
    deck = await db.get(Deck, deck_id)
    if deck is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Deck not found")
    return deck


async def _get_room_or_404(db: AsyncSession, room_id: uuid.UUID) -> Room:
    room = await db.get(Room, room_id)
    if room is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Room not found")
    return room


async def _assert_owns_room(db: AsyncSession, room: Room, user: User) -> None:
    deck = await db.get(Deck, room.deck_id)
    series = await db.get(DeckSeries, deck.series_id)
    await owns_or_super_admin(series.owner_id, user)


@router.post("/decks/{deck_id}/rooms", response_model=RoomOut)
async def create_or_get_active_room(
    deck_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> RoomOut:
    deck = await _get_deck_or_404(db, deck_id)
    series = await db.get(DeckSeries, deck.series_id)
    await owns_or_super_admin(series.owner_id, user)

    active = (
        await db.execute(
            select(Room).where(Room.deck_id == deck_id, Room.status == RoomStatus.ACTIVE)
        )
    ).scalar_one_or_none()
    if active is not None:
        return active

    room = Room(deck_id=deck_id)
    db.add(room)
    await db.commit()
    await db.refresh(room)
    return room


@router.get("/rooms/{room_id}", response_model=RoomOut)
async def get_room(room_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> RoomOut:
    return await _get_room_or_404(db, room_id)


@router.post("/rooms/{room_id}/advance", response_model=RoomOut)
async def advance_slide(
    room_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> RoomOut:
    room = await _get_room_or_404(db, room_id)
    await _assert_owns_room(db, room, user)
    if room.status != RoomStatus.ACTIVE:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Room is not active")

    room.current_slide_index += 1
    await db.commit()
    await db.refresh(room)
    await emit_slide_changed(str(room.id), room.current_slide_index)
    return room


@router.post("/rooms/{room_id}/back", response_model=RoomOut)
async def go_back_slide(
    room_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> RoomOut:
    room = await _get_room_or_404(db, room_id)
    await _assert_owns_room(db, room, user)
    if room.status != RoomStatus.ACTIVE:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Room is not active")

    room.current_slide_index = max(0, room.current_slide_index - 1)
    await db.commit()
    await db.refresh(room)
    await emit_slide_changed(str(room.id), room.current_slide_index)
    return room


@router.post("/rooms/{room_id}/end", response_model=RoomOut)
async def end_room(
    room_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> RoomOut:
    room = await _get_room_or_404(db, room_id)
    await _assert_owns_room(db, room, user)

    room.status = RoomStatus.ENDED
    room.ended_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(room)
    await emit_presentation_ended(str(room.id))
    return room


@router.post("/rooms/{room_id}/checkin", response_model=CheckinResponse)
async def checkin(
    room_id: uuid.UUID,
    body: CheckinRequest,
    db: AsyncSession = Depends(get_db),
) -> CheckinResponse:
    room = await _get_room_or_404(db, room_id)

    join_order = (
        await db.execute(select(func.count()).select_from(Participant).where(Participant.room_id == room_id))
    ).scalar_one() + 1

    device_type = browser = os_name = None
    if body.user_agent:
        parsed = parse_user_agent(body.user_agent)
        device_type = "mobile" if parsed.is_mobile else ("tablet" if parsed.is_tablet else "desktop")
        browser = parsed.browser.family
        os_name = parsed.os.family

    participant = Participant(
        room_id=room_id,
        display_name=body.display_name,
        join_order=join_order,
        device_type=device_type,
        browser=browser,
        os=os_name,
        location_opt_in=body.location_opt_in,
        latitude=body.latitude if body.location_opt_in else None,
        longitude=body.longitude if body.location_opt_in else None,
    )
    db.add(participant)
    await db.commit()
    await db.refresh(participant)

    return CheckinResponse(
        participant_id=participant.id,
        resolved_name=participant.resolved_name,
        room=room,
    )


@router.post("/rooms/{room_id}/react")
async def react(
    room_id: uuid.UUID,
    body: ReactRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    room = await _get_room_or_404(db, room_id)
    if room.status != RoomStatus.ACTIVE:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Room is not active")

    participant = await db.get(Participant, body.participant_id)
    if participant is None or participant.room_id != room_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown participant for this room")

    reaction = Reaction(
        room_id=room_id,
        participant_id=body.participant_id,
        emoji_type=body.emoji_type,
        slide_index=room.current_slide_index,
    )
    db.add(reaction)
    await db.commit()

    await emit_reaction(str(room_id), body.emoji_type.value)
    return {"ok": True}
