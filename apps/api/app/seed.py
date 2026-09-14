import asyncio
import os

from sqlalchemy import select

from app.database import SessionLocal, init_models
from app.models import Role, User
from app.security import hash_password


async def seed_super_admin() -> None:
    await init_models()
    email = os.environ["SEED_SUPER_ADMIN_EMAIL"]
    password = os.environ["SEED_SUPER_ADMIN_PASSWORD"]

    async with SessionLocal() as db:
        existing = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
        if existing is not None:
            return

        db.add(User(email=email, password_hash=hash_password(password), role=Role.SUPER_ADMIN))
        await db.commit()


if __name__ == "__main__":
    asyncio.run(seed_super_admin())
