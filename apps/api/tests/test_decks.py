from tests.conftest import auth_headers


async def _create_deck(client, token, title="My Talk", content="# Slide 1"):
    response = await client.post(
        "/decks",
        json={"title": title, "source_type": "mdx", "content": content},
        headers=auth_headers(token),
    )
    assert response.status_code == 200
    return response.json()


async def test_create_deck_starts_at_version_1(client, regular_user_token):
    deck = await _create_deck(client, regular_user_token)
    assert len(deck["versions"]) == 1
    assert deck["versions"][0]["version_number"] == 1


async def test_new_version_increments_version_number(client, regular_user_token):
    deck = await _create_deck(client, regular_user_token)
    series_id = deck["id"]

    response = await client.post(
        f"/decks/{series_id}/versions",
        json={"title": "ignored", "source_type": "mdx", "content": "# Slide 1 edited"},
        headers=auth_headers(regular_user_token),
    )
    assert response.status_code == 200
    assert response.json()["version_number"] == 2


async def test_other_user_cannot_add_version_to_someone_elses_deck(
    client, regular_user_token, another_user_token
):
    deck = await _create_deck(client, regular_user_token)

    response = await client.post(
        f"/decks/{deck['id']}/versions",
        json={"title": "ignored", "source_type": "mdx", "content": "hijacked"},
        headers=auth_headers(another_user_token),
    )
    assert response.status_code == 403


async def test_user_only_sees_own_decks(client, regular_user_token, another_user_token):
    await _create_deck(client, regular_user_token, title="Mine")
    await _create_deck(client, another_user_token, title="Theirs")

    response = await client.get("/decks", headers=auth_headers(regular_user_token))
    titles = [d["title"] for d in response.json()]
    assert titles == ["Mine"]


async def test_super_admin_sees_every_deck(client, regular_user_token, super_admin_token):
    await _create_deck(client, regular_user_token, title="Someone's talk")

    response = await client.get("/decks", headers=auth_headers(super_admin_token))
    titles = [d["title"] for d in response.json()]
    assert "Someone's talk" in titles


async def test_diff_between_versions_shows_the_change(client, regular_user_token):
    deck = await _create_deck(client, regular_user_token, content="# Slide 1\nhello")
    series_id = deck["id"]

    await client.post(
        f"/decks/{series_id}/versions",
        json={"title": "ignored", "source_type": "mdx", "content": "# Slide 1\ngoodbye"},
        headers=auth_headers(regular_user_token),
    )

    response = await client.get(
        f"/decks/{series_id}/versions/1/diff/2", headers=auth_headers(regular_user_token)
    )
    assert response.status_code == 200
    diff_text = "\n".join(response.json()["diff"])
    assert "-hello" in diff_text
    assert "+goodbye" in diff_text
