import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.models import ReactionType, Role, RoomStatus, SourceType


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class InviteClaimRequest(BaseModel):
    token: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    id: uuid.UUID
    email: EmailStr
    role: Role
    storage_quota_bytes: int
    storage_used_bytes: int

    model_config = {"from_attributes": True}


class InviteCreateRequest(BaseModel):
    role_to_grant: Role = Role.USER
    expires_in_days: int = 7


class InviteOut(BaseModel):
    token: str
    role_to_grant: Role
    expires_at: datetime

    model_config = {"from_attributes": True}


class DeckCreateRequest(BaseModel):
    title: str
    source_type: SourceType
    content: str


class DeckVersionOut(BaseModel):
    id: uuid.UUID
    series_id: uuid.UUID
    version_number: int
    source_type: SourceType
    created_at: datetime

    model_config = {"from_attributes": True}


class DeckSeriesOut(BaseModel):
    id: uuid.UUID
    title: str
    owner_id: uuid.UUID
    versions: list[DeckVersionOut]

    model_config = {"from_attributes": True}


class RoomOut(BaseModel):
    id: uuid.UUID
    deck_id: uuid.UUID
    status: RoomStatus
    current_slide_index: int

    model_config = {"from_attributes": True}


class CheckinRequest(BaseModel):
    display_name: str | None = None
    user_agent: str | None = None
    location_opt_in: bool = False
    latitude: float | None = None
    longitude: float | None = None


class CheckinResponse(BaseModel):
    participant_id: uuid.UUID
    resolved_name: str
    room: RoomOut


class ReactRequest(BaseModel):
    participant_id: uuid.UUID
    emoji_type: ReactionType
