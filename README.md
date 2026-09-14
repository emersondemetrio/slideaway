# Slideaway

A presentation tool where the audience's phones stay in sync with the presenter, and can react live.

A presenter runs a talk from a room. Everyone in the audience scans a QR code, joins on their own phone, and sees whatever slide the presenter is currently on. They can tap emoji reactions that show up on the shared screen and on everyone else's phone. They can also browse back through earlier slides on their own phone without affecting the presenter.

## Roles

- **Admin** — native Android app. Starts and stops a room, advances and goes back through slides. Not built yet (`apps/mobile/android` is a placeholder).
- **Display** — web page, meant for a laptop plugged into a projector. Mirrors the admin's current slide and shows reactions as they come in.
- **Viewer** — web page, no install. Audience members check in via QR code, see the current slide, can browse back locally, and send reactions.
- **Dashboard** — web page. Create decks, start or resume rooms, invite other users (invite-only signup), view basic metrics.

Every architecture and product decision behind this, including the reasoning, is in `DECISIONS.md`.

## Stack

- `apps/api` — FastAPI (Python), SQLAlchemy (async), Postgres, python-socketio for realtime, hand-rolled JWT auth (access/refresh token exchange, role-based access). Dependencies managed with `uv`.
- `apps/web` — Svelte + Vite (no SvelteKit).
- `apps/mobile/android` — native Kotlin admin app. Placeholder, not built yet.
- MinIO for file storage (deck assets), self-hosted, no managed cloud services.

## Running it locally

```
cp .env.example .env
cp apps/api/.env.example apps/api/.env
cp apps/web/.env.example apps/web/.env
```

Fill in real values in each `.env` file (`MINIO_SECRET_KEY` must match between the root `.env` and `apps/api/.env`; set `JWT_SECRET` to a random string; set `SEED_SUPER_ADMIN_EMAIL` and `SEED_SUPER_ADMIN_PASSWORD` for the first account).

```
docker compose up --build
```

Then create the first account (super-admin):

```
docker compose exec api uv run python -m app.seed
```

- API: http://localhost:8000
- Web: http://localhost:5173
- MinIO console: http://localhost:9001

## Status

This is an early draft. Rooms/decks/auth/reactions work end to end; slide content rendering (actually showing deck content instead of a slide number placeholder), the native Android app, and the message bus/AI-deck-generation features described in `DECISIONS.md` are not built yet.
