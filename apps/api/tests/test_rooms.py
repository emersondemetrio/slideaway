from tests.conftest import auth_headers


async def _create_deck_version_id(client, token, title="My Talk"):
    response = await client.post(
        "/decks",
        json={"title": title, "source_type": "mdx", "content": "# Slide 1"},
        headers=auth_headers(token),
    )
    return response.json()["versions"][0]["id"]


async def test_create_room_is_idempotent(client, regular_user_token):
    deck_version_id = await _create_deck_version_id(client, regular_user_token)

    first = await client.post(
        f"/decks/{deck_version_id}/rooms", headers=auth_headers(regular_user_token)
    )
    second = await client.post(
        f"/decks/{deck_version_id}/rooms", headers=auth_headers(regular_user_token)
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]


async def test_other_user_cannot_create_room_for_someone_elses_deck(
    client, regular_user_token, another_user_token
):
    deck_version_id = await _create_deck_version_id(client, regular_user_token)

    response = await client.post(
        f"/decks/{deck_version_id}/rooms", headers=auth_headers(another_user_token)
    )
    assert response.status_code == 403


async def test_ending_a_room_frees_up_a_new_active_room_for_the_same_deck(
    client, regular_user_token
):
    deck_version_id = await _create_deck_version_id(client, regular_user_token)
    headers = auth_headers(regular_user_token)

    first = await client.post(f"/decks/{deck_version_id}/rooms", headers=headers)
    first_room_id = first.json()["id"]

    await client.post(f"/rooms/{first_room_id}/end", headers=headers)

    second = await client.post(f"/decks/{deck_version_id}/rooms", headers=headers)
    assert second.json()["id"] != first_room_id


async def test_advance_and_back_move_slide_index(client, regular_user_token):
    deck_version_id = await _create_deck_version_id(client, regular_user_token)
    headers = auth_headers(regular_user_token)
    room_id = (await client.post(f"/decks/{deck_version_id}/rooms", headers=headers)).json()["id"]

    await client.post(f"/rooms/{room_id}/advance", headers=headers)
    advanced = await client.post(f"/rooms/{room_id}/advance", headers=headers)
    assert advanced.json()["current_slide_index"] == 2

    back = await client.post(f"/rooms/{room_id}/back", headers=headers)
    assert back.json()["current_slide_index"] == 1


async def test_back_does_not_go_below_zero(client, regular_user_token):
    deck_version_id = await _create_deck_version_id(client, regular_user_token)
    headers = auth_headers(regular_user_token)
    room_id = (await client.post(f"/decks/{deck_version_id}/rooms", headers=headers)).json()["id"]

    response = await client.post(f"/rooms/{room_id}/back", headers=headers)
    assert response.json()["current_slide_index"] == 0


async def test_only_owner_can_advance_room(client, regular_user_token, another_user_token):
    deck_version_id = await _create_deck_version_id(client, regular_user_token)
    room_id = (
        await client.post(
            f"/decks/{deck_version_id}/rooms", headers=auth_headers(regular_user_token)
        )
    ).json()["id"]

    response = await client.post(
        f"/rooms/{room_id}/advance", headers=auth_headers(another_user_token)
    )
    assert response.status_code == 403


async def test_checkin_assigns_participant_number_when_no_name(client, regular_user_token):
    deck_version_id = await _create_deck_version_id(client, regular_user_token)
    room_id = (
        await client.post(
            f"/decks/{deck_version_id}/rooms", headers=auth_headers(regular_user_token)
        )
    ).json()["id"]

    first = await client.post(f"/rooms/{room_id}/checkin", json={})
    second = await client.post(f"/rooms/{room_id}/checkin", json={})

    assert first.json()["resolved_name"] == "Participant #1"
    assert second.json()["resolved_name"] == "Participant #2"


async def test_checkin_parses_device_info_from_user_agent(client, regular_user_token):
    deck_version_id = await _create_deck_version_id(client, regular_user_token)
    room_id = (
        await client.post(
            f"/decks/{deck_version_id}/rooms", headers=auth_headers(regular_user_token)
        )
    ).json()["id"]

    response = await client.post(
        f"/rooms/{room_id}/checkin",
        json={
            "user_agent": (
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
            )
        },
    )
    assert response.status_code == 200


async def test_react_requires_an_active_room(client, regular_user_token):
    deck_version_id = await _create_deck_version_id(client, regular_user_token)
    headers = auth_headers(regular_user_token)
    room_id = (await client.post(f"/decks/{deck_version_id}/rooms", headers=headers)).json()["id"]

    checkin = await client.post(f"/rooms/{room_id}/checkin", json={})
    participant_id = checkin.json()["participant_id"]

    await client.post(f"/rooms/{room_id}/end", headers=headers)

    response = await client.post(
        f"/rooms/{room_id}/react",
        json={"participant_id": participant_id, "emoji_type": "love"},
    )
    assert response.status_code == 400


async def test_react_rejects_participant_from_a_different_room(client, regular_user_token):
    deck_version_id = await _create_deck_version_id(client, regular_user_token)
    headers = auth_headers(regular_user_token)

    room_a = (await client.post(f"/decks/{deck_version_id}/rooms", headers=headers)).json()["id"]

    another_deck_version_id = await _create_deck_version_id(
        client, regular_user_token, title="Second Talk"
    )
    room_b = (
        await client.post(f"/decks/{another_deck_version_id}/rooms", headers=headers)
    ).json()["id"]

    checkin = await client.post(f"/rooms/{room_a}/checkin", json={})
    participant_id = checkin.json()["participant_id"]

    response = await client.post(
        f"/rooms/{room_b}/react",
        json={"participant_id": participant_id, "emoji_type": "wow"},
    )
    assert response.status_code == 400
