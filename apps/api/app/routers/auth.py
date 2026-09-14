import secrets
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user, require_super_admin
from app.models import Invite, RefreshToken, Role, User
from app.schemas import (
    InviteClaimRequest,
    InviteCreateRequest,
    InviteOut,
    LoginRequest,
    RefreshRequest,
    TokenPair,
    UserOut,
)
from app.security import (
    DUMMY_PASSWORD_HASH,
    TokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


async def _issue_token_pair(db: AsyncSession, user: User) -> TokenPair:
    access = create_access_token(user.id, Role(user.role))
    refresh, jti = create_refresh_token(user.id)
    db.add(
        RefreshToken(
            user_id=user.id,
            jti=jti,
            expires_at=datetime.now(UTC) + timedelta(days=7),
        )
    )
    await db.commit()
    return TokenPair(access_token=access, refresh_token=refresh)


@router.post("/invites", response_model=InviteOut)
async def create_invite(
    body: InviteCreateRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_super_admin),
) -> InviteOut:
    invite = Invite(
        token=secrets.token_urlsafe(32),
        role_to_grant=body.role_to_grant,
        created_by=admin.id,
        expires_at=datetime.now(UTC) + timedelta(days=body.expires_in_days),
    )
    db.add(invite)
    await db.commit()
    await db.refresh(invite)
    return invite


@router.post("/invites/claim", response_model=TokenPair)
async def claim_invite(body: InviteClaimRequest, db: AsyncSession = Depends(get_db)) -> TokenPair:
    invite = (
        await db.execute(select(Invite).where(Invite.token == body.token))
    ).scalar_one_or_none()

    if invite is None or invite.claimed_at is not None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invite invalid or already claimed")
    if invite.expires_at < datetime.now(UTC):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invite expired")

    existing = (
        await db.execute(select(User).where(User.email == body.email))
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email already registered")

    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        role=invite.role_to_grant,
    )
    db.add(user)
    await db.flush()

    invite.claimed_by = user.id
    invite.claimed_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(user)

    return await _issue_token_pair(db, user)


@router.post("/login", response_model=TokenPair)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenPair:
    user = (
        await db.execute(select(User).where(User.email == body.email))
    ).scalar_one_or_none()

    password_hash = user.password_hash if user is not None else DUMMY_PASSWORD_HASH
    password_ok = verify_password(body.password, password_hash)

    if user is None or not password_ok:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")

    return await _issue_token_pair(db, user)


@router.post("/refresh", response_model=TokenPair)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)) -> TokenPair:
    try:
        payload = decode_token(body.refresh_token)
    except TokenError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token") from exc

    if payload.get("type") != "refresh":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not a refresh token")

    stored = (
        await db.execute(select(RefreshToken).where(RefreshToken.jti == payload["jti"]))
    ).scalar_one_or_none()
    if stored is None or stored.revoked_at is not None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Refresh token revoked or unknown")

    user = await db.get(User, uuid.UUID(payload["sub"]))
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User no longer exists")

    stored.revoked_at = datetime.now(UTC)
    await db.commit()

    return await _issue_token_pair(db, user)


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)) -> UserOut:
    return user
