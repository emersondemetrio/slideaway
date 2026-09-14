import secrets
import uuid
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from app.config import settings
from app.models import ROLE_RANK, Role


class TokenError(Exception):
    pass


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


DUMMY_PASSWORD_HASH = hash_password(secrets.token_urlsafe(32))


def _encode(payload: dict, ttl: timedelta) -> str:
    now = datetime.now(UTC)
    to_encode = {**payload, "iat": now, "exp": now + ttl}
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: uuid.UUID, role: Role) -> str:
    return _encode(
        {"sub": str(user_id), "role": role.value, "type": "access"},
        timedelta(minutes=settings.access_token_ttl_minutes),
    )


def create_refresh_token(user_id: uuid.UUID) -> tuple[str, str]:
    jti = str(uuid.uuid4())
    token = _encode(
        {"sub": str(user_id), "jti": jti, "type": "refresh"},
        timedelta(days=settings.refresh_token_ttl_days),
    )
    return token, jti


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise TokenError(str(exc)) from exc


def role_at_least(user_role: Role, required: Role) -> bool:
    return ROLE_RANK[user_role] >= ROLE_RANK[required]
