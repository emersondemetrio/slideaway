import os
import urllib.parse

import asyncpg
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.database import Base, get_db
from app.main import api
from app.models import Role, User
from app.security import hash_password

TEST_PASSWORD = "test-password-123"

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://slideaway:slideaway@localhost:5433/slideaway_test",
)

test_engine = create_async_engine(TEST_DATABASE_URL)


async def _ensure_test_database_exists() -> None:
    parsed = urllib.parse.urlparse(TEST_DATABASE_URL.replace("+asyncpg", ""))
    target_db = parsed.path.lstrip("/")

    conn = await asyncpg.connect(
        user=parsed.username,
        password=parsed.password,
        host=parsed.hostname,
        port=parsed.port,
        database="postgres",
    )
    try:
        exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", target_db)
        if not exists:
            await conn.execute(f'CREATE DATABASE "{target_db}"')
    finally:
        await conn.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _schema():
    await _ensure_test_database_exists()
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    await test_engine.dispose()


@pytest_asyncio.fixture
async def db_session():
    async with test_engine.connect() as conn:
        await conn.begin()
        session = AsyncSession(bind=conn, join_transaction_mode="create_savepoint", expire_on_commit=False)
        try:
            yield session
        finally:
            await session.close()
            await conn.rollback()


@pytest_asyncio.fixture
async def client(db_session):
    async def _override_get_db():
        yield db_session

    api.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=api)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    api.dependency_overrides.clear()


async def _make_user(db_session: AsyncSession, email: str, role: Role) -> User:
    user = User(email=email, password_hash=hash_password(TEST_PASSWORD), role=role)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def super_admin(db_session):
    return await _make_user(db_session, "super-admin@example.com", Role.SUPER_ADMIN)


@pytest_asyncio.fixture
async def regular_user(db_session):
    return await _make_user(db_session, "user@example.com", Role.USER)


@pytest_asyncio.fixture
async def another_user(db_session):
    return await _make_user(db_session, "other-user@example.com", Role.USER)


async def _login(client: AsyncClient, email: str) -> str:
    response = await client.post("/auth/login", json={"email": email, "password": TEST_PASSWORD})
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest_asyncio.fixture
async def super_admin_token(client, super_admin):
    return await _login(client, super_admin.email)


@pytest_asyncio.fixture
async def regular_user_token(client, regular_user):
    return await _login(client, regular_user.email)


@pytest_asyncio.fixture
async def another_user_token(client, another_user):
    return await _login(client, another_user.email)


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
