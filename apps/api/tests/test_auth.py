from datetime import UTC, datetime, timedelta

from app.models import Invite, Role
from tests.conftest import TEST_PASSWORD, auth_headers


async def test_login_wrong_password_returns_401(client, regular_user):
    response = await client.post(
        "/auth/login", json={"email": regular_user.email, "password": "wrong-password"}
    )
    assert response.status_code == 401


async def test_login_unknown_email_returns_401(client):
    response = await client.post(
        "/auth/login", json={"email": "nobody@example.com", "password": "whatever"}
    )
    assert response.status_code == 401


async def test_login_success_returns_token_pair(client, regular_user):
    response = await client.post(
        "/auth/login", json={"email": regular_user.email, "password": TEST_PASSWORD}
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body


async def test_me_requires_authentication(client):
    response = await client.get("/auth/me")
    assert response.status_code == 401


async def test_me_returns_current_user(client, regular_user_token, regular_user):
    response = await client.get("/auth/me", headers=auth_headers(regular_user_token))
    assert response.status_code == 200
    assert response.json()["email"] == regular_user.email


async def test_only_super_admin_can_create_invites(client, regular_user_token):
    response = await client.post(
        "/auth/invites",
        json={"role_to_grant": "user", "expires_in_days": 7},
        headers=auth_headers(regular_user_token),
    )
    assert response.status_code == 403


async def test_super_admin_can_create_invite_and_it_can_be_claimed(client, super_admin_token):
    create_response = await client.post(
        "/auth/invites",
        json={"role_to_grant": "user", "expires_in_days": 7},
        headers=auth_headers(super_admin_token),
    )
    assert create_response.status_code == 200
    token = create_response.json()["token"]

    claim_response = await client.post(
        "/auth/invites/claim",
        json={"token": token, "email": "invited@example.com", "password": "some-password"},
    )
    assert claim_response.status_code == 200
    assert "access_token" in claim_response.json()


async def test_invite_cannot_be_claimed_twice(client, super_admin_token):
    create_response = await client.post(
        "/auth/invites",
        json={"role_to_grant": "user", "expires_in_days": 7},
        headers=auth_headers(super_admin_token),
    )
    token = create_response.json()["token"]

    first = await client.post(
        "/auth/invites/claim",
        json={"token": token, "email": "first-claim@example.com", "password": "some-password"},
    )
    assert first.status_code == 200

    second = await client.post(
        "/auth/invites/claim",
        json={"token": token, "email": "second-claim@example.com", "password": "some-password"},
    )
    assert second.status_code == 400


async def test_expired_invite_cannot_be_claimed(client, db_session, super_admin):
    invite = Invite(
        token="expired-token",
        role_to_grant=Role.USER,
        created_by=super_admin.id,
        expires_at=datetime.now(UTC) - timedelta(days=1),
    )
    db_session.add(invite)
    await db_session.commit()

    response = await client.post(
        "/auth/invites/claim",
        json={"token": "expired-token", "email": "late@example.com", "password": "some-password"},
    )
    assert response.status_code == 400


async def test_refresh_rotates_token_and_revokes_old_one(client, regular_user):
    login = await client.post(
        "/auth/login", json={"email": regular_user.email, "password": TEST_PASSWORD}
    )
    old_refresh_token = login.json()["refresh_token"]

    refreshed = await client.post("/auth/refresh", json={"refresh_token": old_refresh_token})
    assert refreshed.status_code == 200

    reused = await client.post("/auth/refresh", json={"refresh_token": old_refresh_token})
    assert reused.status_code == 401
