import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class Role(str, enum.Enum):
    USER = "user"
    SUPER_ADMIN = "super_admin"


ROLE_RANK = {Role.USER: 1, Role.SUPER_ADMIN: 2}


class SourceType(str, enum.Enum):
    PDF = "pdf"
    IMAGE_SET = "image_set"
    MDX = "mdx"


class RoomStatus(str, enum.Enum):
    ACTIVE = "active"
    ENDED = "ended"


class ReactionType(str, enum.Enum):
    LIKE = "like"
    LOVE = "love"
    HAHA = "haha"
    YAY = "yay"
    WOW = "wow"
    SAD = "sad"
    ANGRY = "angry"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = _uuid_pk()
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(String(20), default=Role.USER)
    storage_quota_bytes: Mapped[int] = mapped_column(Integer, default=500 * 1024 * 1024)
    storage_used_bytes: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    deck_series: Mapped[list["DeckSeries"]] = relationship(back_populates="owner")


class Invite(Base):
    __tablename__ = "invites"

    id: Mapped[uuid.UUID] = _uuid_pk()
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    role_to_grant: Mapped[Role] = mapped_column(String(20), default=Role.USER)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    claimed_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    claimed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    expires_at: Mapped[datetime]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    jti: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(nullable=True)
    expires_at: Mapped[datetime]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class DeckSeries(Base):
    __tablename__ = "deck_series"

    id: Mapped[uuid.UUID] = _uuid_pk()
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    owner: Mapped["User"] = relationship(back_populates="deck_series")
    versions: Mapped[list["Deck"]] = relationship(back_populates="series", order_by="Deck.version_number")


class Deck(Base):
    __tablename__ = "decks"
    __table_args__ = (UniqueConstraint("series_id", "version_number", name="uq_deck_series_version"),)

    id: Mapped[uuid.UUID] = _uuid_pk()
    series_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("deck_series.id"))
    version_number: Mapped[int] = mapped_column(Integer)
    source_type: Mapped[SourceType] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    series: Mapped["DeckSeries"] = relationship(back_populates="versions")
    rooms: Mapped[list["Room"]] = relationship(back_populates="deck")


class Room(Base):
    __tablename__ = "rooms"
    __table_args__ = (
        Index(
            "uq_one_active_room_per_deck",
            "deck_id",
            unique=True,
            postgresql_where=text("status = 'active'"),
        ),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    deck_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("decks.id"))
    status: Mapped[RoomStatus] = mapped_column(String(20), default=RoomStatus.ACTIVE)
    current_slide_index: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    ended_at: Mapped[datetime | None] = mapped_column(nullable=True)

    deck: Mapped["Deck"] = relationship(back_populates="rooms")
    participants: Mapped[list["Participant"]] = relationship(back_populates="room")
    reactions: Mapped[list["Reaction"]] = relationship(back_populates="room")


class Participant(Base):
    __tablename__ = "participants"

    id: Mapped[uuid.UUID] = _uuid_pk()
    room_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("rooms.id"))
    display_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    join_order: Mapped[int] = mapped_column(Integer)
    device_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    browser: Mapped[str | None] = mapped_column(String(50), nullable=True)
    os: Mapped[str | None] = mapped_column(String(50), nullable=True)
    location_opt_in: Mapped[bool] = mapped_column(default=False)
    latitude: Mapped[float | None] = mapped_column(nullable=True)
    longitude: Mapped[float | None] = mapped_column(nullable=True)
    joined_at: Mapped[datetime] = mapped_column(server_default=func.now())

    room: Mapped["Room"] = relationship(back_populates="participants")

    @property
    def resolved_name(self) -> str:
        return self.display_name or f"Participant #{self.join_order}"


class Reaction(Base):
    __tablename__ = "reactions"

    id: Mapped[uuid.UUID] = _uuid_pk()
    room_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("rooms.id"))
    participant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("participants.id"))
    emoji_type: Mapped[ReactionType] = mapped_column(String(20))
    slide_index: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    room: Mapped["Room"] = relationship(back_populates="reactions")
