import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Role, User
from app.security import TokenError, decode_token, role_at_least

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if token is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    try:
        payload = decode_token(token)
    except TokenError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token") from exc

    if payload.get("type") != "access":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not an access token")

    user = await db.get(User, uuid.UUID(payload["sub"]))
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User no longer exists")
    return user


def require_role(minimum: Role):
    async def _check(user: User = Depends(get_current_user)) -> User:
        if not role_at_least(Role(user.role), minimum):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient role")
        return user

    return _check


require_user = require_role(Role.USER)
require_super_admin = require_role(Role.SUPER_ADMIN)


async def owns_or_super_admin(resource_owner_id: uuid.UUID, user: User) -> None:
    if user.role == Role.SUPER_ADMIN:
        return
    if resource_owner_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not your resource")
