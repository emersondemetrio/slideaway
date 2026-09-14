# Slideaway - MVP Task List

Every task has a code, `SA-NNN`, referenced in commits/branches/PRs. Status: `todo`, `doing`, `done`. This file tracks what's left for a working MVP, not the reasoning behind past decisions - that's `DECISIONS.md`.

Working assumption, stated explicitly since it changes scope a lot: **"ADMIN ready" means the Dashboard web surface (deck/room management, invites, metrics) is usable end to end, plus a web-based way to actually run a live room (create/advance/back/end) so a presenter isn't blocked on the native Android app existing.** The native app itself is tracked separately below and is not MVP-blocking, per the existing decision in `DECISIONS.md` that it's a later phase. Flag if this reading is wrong.

## Core loop (Viewer/Display) - blocks everything else, do first

- [ ] **SA-001** - Display.svelte never fetches the room's current state on mount, only listens for socket events. A page load or reconnect mid-presentation shows slide 1 until the next `slide_changed` event, which may be long after the real current slide. Fetch `GET /rooms/:id` on mount, same as Viewer's checkin already does.
- [ ] **SA-002** - Real slide content rendering in Viewer.svelte, replacing the "Slide N" placeholder. Needs an API endpoint (SA-010) to resolve a room's deck content for a given slide index.
- [ ] **SA-003** - Same real content rendering in Display.svelte, sharing the render component with SA-002.
- [ ] **SA-004** - MDX rendering path (source_type `mdx`): parse and render the deck's Markdown/MDX content for the current slide.
- [ ] **SA-005** - PDF/image rendering path (source_type `pdf`/`image_set`): fetch the relevant asset from MinIO via a presigned URL and display it.

## API work this will likely unblock (fork into a separate branch/PR when hit)

- [ ] **SA-010** - Endpoint to resolve a room's actual slide content for its `current_slide_index` (not just the index itself, which `GET /rooms/:id` already returns).
- [ ] **SA-011** - Deck asset upload endpoint - `storage.py` already has `put_asset`/`presigned_get_url` but nothing routes to them yet.
- [ ] **SA-012** - Storage quota enforcement: check `storage_used_bytes` vs `storage_quota_bytes` before accepting an upload, update `storage_used_bytes` after.
- [ ] **SA-013** - Alembic migrations, replacing `Base.metadata.create_all` (already flagged as a near-term follow-up in `DECISIONS.md`).

## Dashboard (ADMIN surface)

- [ ] **SA-020** - Deck creation form: title + MDX content (textarea), or file upload for pdf/image_set (depends on SA-011).
- [ ] **SA-021** - Deck version history + diff view, using the existing `/decks/{series_id}/versions/{a}/diff/{b}` endpoint.
- [ ] **SA-022** - Web-based room remote control (advance/back/end) so a presenter can run a room from any browser before the native app exists. This is the concrete "ADMIN ready without the native app" deliverable.
- [ ] **SA-023** - Room list + per-room metrics view (attendance count, device breakdown, reaction counts) for a deck. Needs an aggregation endpoint - not built yet.
- [ ] **SA-024** - Super-admin cross-user visibility: list all users' rooms/decks, not just decks (decks already respect the role check; rooms don't have an equivalent "list" endpoint at all yet).
- [ ] **SA-025** - Quota usage display for the current user, and a super-admin UI to adjust another user's quota.

## Native mobile - not MVP-blocking, tracked for later

- [ ] **SA-030** - Kotlin/Jetpack Compose admin app scaffold.
- [ ] **SA-031** - Socket.IO Java client + on-device JWT auth flow.

## Infra / ops

- [ ] **SA-040** - CI pipeline: run backend `pytest` and frontend `vitest` on every PR, `ruff`/`npm audit` as gates.
- [ ] **SA-041** - Confirm CodeRabbit's actual plan status for this repo (public-repo free tier vs the default trial - open question from the conversation, not yet checked).
- [ ] **SA-042** - Deployment docs/scripts for the Hostinger VPS.

## Explicitly out of MVP scope (already decided as fast-follow in DECISIONS.md, listed here only for traceability)

- **SA-050** - Message bus (Kafka/NATS) phase.
- **SA-051** - AI-assisted deck generation.
- **SA-052** - Push notifications.
- **SA-053** - Full in-app slide editor.
- **SA-054** - Reaction palette customization.

## Also open, not code-shaped

- Licensing decision before real launch (BUSL vs staying permissive) - see `DECISIONS.md`.
