# Slideaway - Decision Log

## Open decision: licensing before launch

Repo currently ships Apache 2.0, public, from the initial commit. Under a permissive license, anyone (including a well-funded competitor) can clone this once it has real traction, self-host it, and sell it, with no obligation beyond keeping the license notice - which is a direct conflict with the stated goal of eventually selling usage of this product.

**Not urgent today** - nobody forks a scaffold with no users. But license changes are not retroactive: anything already released under Apache 2.0 stays Apache 2.0 forever for whoever already has it. Only future commits can carry a different license, so this needs a conscious decision before real traction/marketing, not after.

**Likely direction when that day comes:** Business Source License (BUSL/BSL) - source-available, not OSI-approved open source. Anyone can view/use/modify for internal use or testing, but competing production/commercial use requires a paid agreement, and each version auto-converts to a fully open license (commonly Apache 2.0) after a set number of years (commonly ~4). Used by Sentry, CockroachDB, and (controversially) Redis for exactly this reason. The Functional Source License is a simpler, newer alternative in the same spirit.

**Open uncertainty:** CodeRabbit's free-forever tier is specifically for open-source projects, and BUSL is explicitly not OSI-approved open source. Unconfirmed whether switching would knock the repo out of that free tier - check when this decision actually gets made.

## Repo layout & build tooling

- **Classic monorepo**, not a flat `backend/`/`frontend/` split:
  ```
  apps/
    api/            FastAPI backend
    web/             Svelte web frontend (viewer/display/dashboard)
    mobile/android/  native Kotlin admin app - not built yet, placeholder only
  packages/          shared contracts across apps - empty until something's worth sharing
  docker-compose.yml
  ```
- **Python dependency management: `uv`** (not pip/poetry/pipenv). `uv.lock` is committed for reproducibility.
- **Zero comments in code, project-wide** - see `CLAUDE.md`. Any rationale worth keeping lives in this file, not inline.
- Auth deep-dive learning goals (authn/authz/token exchange/RBAC decorator) are implemented via FastAPI's actual idiom - dependency injection (`Depends`), not Python decorators. `require_role()` in `apps/api/app/deps.py` is the "@admin decorator" equivalent.
- Alembic is wired into the dependency set but not yet used for migrations - the draft bootstraps schema via `Base.metadata.create_all` on startup. First real Alembic migration is a near-term follow-up once the schema stabilizes.
- Room's "one active room per deck" idempotency invariant is enforced twice: application-level get-or-create logic, **and** a Postgres partial unique index (`WHERE status = 'active'`) as defense in depth.
- State-changing actions (advance/back/end/checkin/react) all go through authenticated-or-open REST endpoints, which persist to Postgres and then trigger a Socket.IO broadcast server-side. The client's Socket.IO connection is receive-only (`join_room`/`leave_room` to subscribe to broadcasts) - it never sends mutations directly over the socket.
- **Security audit pass on this draft:** `ruff check` clean on the backend (one FastAPI-specific false positive, B008 on `Depends()` in argument defaults, explicitly ignored in `pyproject.toml` - that's required FastAPI style, not a bug). `npm audit` on the frontend found a moderate dev-server-only esbuild vulnerability (GHSA-67mh-4wv8-2f99, affects `vite`'s dev server, not production builds); fixed by upgrading `vite` 5->6 and `@sveltejs/vite-plugin-svelte` 4->5 (a clean, non-breaking upgrade path for this project) rather than ignoring it - `npm audit` now reports zero vulnerabilities.
- **First real smoke test caught two live bugs, both fixed:** (1) `minio/minio` no longer exists on Docker Hub (MinIO removed their Docker Hub org in October 2025) - `docker-compose.yml` now pulls `quay.io/minio/minio` instead. (2) Every datetime column in `models.py` was declared timezone-naive by default, while application code writes timezone-aware datetimes (`datetime.now(UTC)`) - Postgres/asyncpg rejected the mix on the very first login. All datetime columns are now explicitly `DateTime(timezone=True)`. After both fixes, the full loop (login, create deck, idempotent room creation verified to return the same room on a repeated call, anonymous check-in, admin advance, viewer reaction) was run against the real Docker Compose stack and works end to end.
- Automated test suites (backend `pytest`, frontend `vitest`) are being added on a separate branch/PR, not committed straight to `main`.

Running log of product/architecture decisions, captured as they're made. Append-only; when a decision is revisited, mark the old entry superseded rather than deleting it.

## Product concept

Interactive, real-time presentation tool. A presenter runs a live talk; the audience joins on their own phones via QR code to receive synced content and send live reactions.

## Open Questions
- Should we buy slideaway.app?

## Core interaction loop

- Admin controls slide position: start/stop the presentation, advance, go back.
- Slide position broadcasts in real time to the Display and every connected Viewer.
- Viewers can navigate backward locally (browse earlier slides on their own phone) but cannot go forward past the presenter's current live position - local position snaps back to the live ceiling.
- Viewers send emoji reactions by tapping. Reactions are a **full broadcast**: shown on the shared Display screen *and* on every Viewer's phone, aggregated/anonymous (not attributed to the sender on shared screens).
- **Reaction palette (v1): fixed set**, Facebook-reactions-style - Like, Love, Haha, Yay, Wow, Sad, Angry. Customizable/presenter-chosen palettes are **fast-follow**, not MVP.
- **Reaction rendering on Display: both** a persistent per-emoji tally (reactive counter, so a quiet trickle still reads as "something happening") and an ephemeral float-up-and-fade burst animation per incoming reaction (Svelte `transition:fly`/`animate:flip`).

## Roles (three distinct clients)

- **Admin** - single native Android app (Kotlin + Jetpack Compose). Controls: start/stop, advance/back. Single platform (Android only), single admin (the user) for now - revisit if multi-admin or iOS support becomes necessary.
- **Display** - web only. A browser tab on a laptop connected to a projector; mirrors admin's current state; renders the slide plus the full reaction broadcast overlay.
- **Viewer** - web only, **permanently** (not a stopgap): zero-install is a hard UX requirement of the QR-scan-mid-talk flow. Joins via QR code check-in; optional display name, otherwise auto-assigned "Participant #N"; receives synced slide content; can navigate back locally (not forward); has an emoji-react control.

## Room / multi-tenancy model

- Multi-room from day one: cheap to build in now, expensive to retrofit later.
- URL scheme: `slideaway.com/rooms/<uuid>/{admin|display|viewer}`.
- Real-world usage is expected to be single-room-at-a-time, but the architecture doesn't assume that.
- **End of presentation:** admin broadcasts a "presentation ended" event to every connected client; Display and all Viewers lock to a final screen, no further interaction.
- **Late join:** check-in is open for the entire life of the room, not just a pre-presentation lobby - a Viewer can scan in at any point mid-talk and lands directly on the presenter's current live slide (no "start from slide 1 and catch up").
- **Local back-navigation vs live position:** when a Viewer browses back to an earlier slide and the presenter advances further, the Viewer's screen does **not** auto-snap forward - it stays put. A blinking 🟢 indicator appears top-right once they've drifted from the live position, as the affordance to jump back to live.
- **Persistence: everything, always.** Rooms and their history are never deleted - check-ins, reactions, timing, are all kept as a permanent record. No ephemeral/throwaway rooms.

## Metrics & Admin Dashboard

- Track audience/session metrics per room: attendance count, device/client info, reaction activity, etc. ("just because" - exploratory/nice-to-have, not tied to one specific business need yet).
- A **web dashboard** (separate surface from the native Android admin app) for reviewing this data after the fact - likely additional routes in the same Svelte app (e.g. `/rooms/<uuid>/dashboard`, possibly a global `/dashboard` across rooms).
- **Device metrics: basic, non-PII only** - device type/OS/browser derived from user-agent, tied to the anonymous participant ID. Location is **opt-in only**, never collected by default.
- **Deck management (create/upload/list decks, "create room from this deck") lives in the dashboard**, not the native app - for now. The native admin app stays narrow: join an already-created room and control it live (start/stop, advance/back). Noted: these surfaces are expected to reach feature parity eventually - this is a v1 scoping choice, not a permanent architectural split.

## Slide content model

- v1 supports two content sources:
  - **(a) PDF/image import** - slice pages/images, display as-is.
  - **(b) Rich Markdown/MDX rendering** - text-authored (headings, code blocks, images, embedded components), no WYSIWYG editor required.
- **(c) Full in-app slide editor** (Google-Slides-style authoring) is explicitly **out of scope** for now. Documented here as potential future work, not being built.
- **(d) AI-assisted deck creation** - chat with an agent to generate a deck. **Fast-follow, not MVP** (same reasoning as the message bus: get the core loop working with manual MDX/PDF first). Slots in cleanly because it only needs to *produce* MDX - no new rendering engine, it feeds the same pipeline as (b).
- **Decks and rooms are separate entities**, both UUID-identified: a deck is saved once and can spin up multiple rooms (repeat deliveries of the same talk each get their own fresh room/UUID/history). A room references its deck by UUID.
- Deck sharing (private vs shareable) - **moot for now**: there's only one admin account in the whole system, so "share with whom" has no answer to attach to yet. Revisit if/when multi-admin exists.

## Idempotent room creation

- **All IDs are server-generated.** Clients (native admin app, web dashboard, web viewer/display) never mint identifiers - they only view/send data.
- Because the client can't hand back a client-generated UUID or idempotency key, idempotency is enforced via **server-side state**: at most one *active* (not-yet-ended) room per deck. "Create room" really means "get-or-create the active room for this deck" - if an active room already exists for that `deck_id`, it's returned as-is; otherwise a new one is created. A double-tap or retried request against the same deck can never spin up two competing live rooms, because the server dedupes against its own state, not a client-supplied token.
- Once a room's presentation ends, its deck's "active room" slot frees up and the next create call for that deck mints a genuinely new room.

## Frontend (Viewer + Display)

- **Svelte + Vite** (no SvelteKit - SSR/routing machinery isn't needed for a purely socket-driven realtime client app).
  - *Why:* the audience-facing Viewer loads mid-talk over venue wifi, so bundle size/load time matter - Svelte compiles away the framework instead of shipping a runtime + virtual DOM. The app is fundamentally "small pieces of state updating frequently from socket events" (slide index, reaction bursts), which fits Svelte's reactivity model directly. Built-in `transition:`/`animate:` directives suit reaction-burst and slide-transition animations without reaching for an animation library.
  - *Alternatives considered:* React/Next.js (the "bigger ecosystem" argument doesn't carry much weight for a solo/learning project - no hiring-pool or team-scale concern here); Solid (not chosen, no specific reason to prefer it over Svelte for this case).

## Backend

- **FastAPI** (Python) - stated preference ("just because"), no further requirement behind it.
- **Realtime transport: `python-socketio`.** Rooms/namespaces/reconnect/ack come built in, and it ships an official Java client that the native Kotlin admin app can use directly - same protocol semantics on web and native.
  - *Alternatives considered:* raw FastAPI `WebSocket` (rejected for MVP - would mean hand-rolling reconnect/backoff/room-membership across three separate clients: web JS, and the Kotlin admin app); a dedicated pub/sub gateway like Centrifugo (not pursued - adds an extra service before the core loop even works, revisit only if `python-socketio` becomes a bottleneck).
- **Wire format: JSON.** We considered protobuf but decided to go with JSON for this MVP - Socket.IO's JS/Java clients auto-serialize JSON natively, and client-facing payloads are tiny (slide index, emoji code, participant id), so protobuf's ergonomics cost isn't worth paying there. Protobuf is earmarked instead for the future message-bus phase (server-to-server event schemas), where it's a more natural fit alongside Kafka/NATS.

## Push notifications

- **Fast-follow - may not even be needed.** Scoped to the native admin app only (Viewers are one-session/anonymous, not a realistic push audience). Candidate triggers: someone checks into your room, a PDF import finishes processing, an invited user claims their invite link.
- Note for later: Android push delivery fundamentally requires **Firebase Cloud Messaging** - there's no realistic self-hosted alternative (UnifiedPush exists but needs the recipient to install a separate distributor app). If/when this gets built, FCM is a deliberate, accepted exception to the "everything I can install" infra rule, same category as the earlier Auth0-vs-self-hosted tradeoff.

## Explicit learning goals

This project is deliberately also a vehicle to (re)learn: **Python**, **pub/sub architecture**, and **FastAPI**. When a technical choice has both a "fastest to ship" option and a "more instructive" option, that's worth surfacing explicitly rather than silently defaulting to the fastest path - the learning value is a real project goal, not just a side effect.

## Roles & multi-tenancy (supersedes earlier single-admin framing)

**This is a real multi-tenant product**, not a personal tool with one hardcoded admin. Three-tier role model:

- **super-admin** (the user, platform owner) - genuinely global power: full visibility/management over *every* user's decks, rooms, and dashboards (not scoped to their own content), plus account provisioning (invite users, set storage quotas). Role model is a strict nested hierarchy - `viewer ⊂ user ⊂ super-admin` - implemented as an ordinal role check (`role >= required_role`) rather than separate per-role permission flags. Cross-user access for `super-admin` specifically means resource-ownership filters (`WHERE user_id = current_user.id`) are bypassed entirely when the caller is `super-admin`.
- **user** (any registered presenter) - creates and administers their own decks and rooms. This is what earlier sections of this doc called "Admin"/"the admin app" when the model was single-admin-only - every `user` now gets that same capability for their own content, not just the platform owner.
- **Viewer** - unchanged: anonymous, per-room, no account, joins via QR/room code.

**Signup: invite-only via invite link.** Super-admin generates a unique invite-token link; the invited person opens it to claim their account (sets their own password) rather than the super-admin picking credentials for them. No transactional email service - the link is shared manually, out-of-band (text/whatever), matching "no budget for email sending." The super-admin account itself is **seeded** (created via a seed script/initial migration, not through any signup or invite path) so there's always at least one account without needing the invite flow to bootstrap itself.

**Reopened by this change** (previously answered under a single-admin assumption, now need revisiting):
- Deck sharing - **resolved: strictly single-owner.** One `user_id` per deck, no cross-user access/collaboration. Revisit only if a real need for it shows up later.
- Native Android admin app auth - previously implicitly single-hardcoded-admin. Now needs to authenticate as *whichever user* is signed in, not one fixed identity.
- Storage quotas - **resolved: 500MB per user by default**, enforced via a `storage_quota_bytes` field on the account. This is a per-account, super-admin-adjustable value (not a hardcoded global constant) - super-admin can raise/lower an individual user's quota via the provisioning/account-management screen. (Single-upload size cap left as a smaller implementation default, well under the quota, to avoid one file eating a whole account's allowance - exact number not yet pinned, low stakes.)
- Dashboard scope - presumably becomes per-user (a `user` sees only their own rooms/decks/metrics; `super-admin` may see across all users).

## Admin authentication

- **Hand-rolled JWT auth**, self-hosted - no Auth0, no managed IdP. Chosen deliberately as a deep-dive learning exercise into: authentication (login endpoint issuing tokens), authorization (role checks), token exchange (access + refresh token flow), and securing endpoints via a reusable guard - e.g. an `@admin`-style dependency/decorator on FastAPI routes that aren't public.
  - *Alternatives considered:* Auth0 free tier (rejected - managed SaaS, breaks the "everything I can install" rule, and teaches SDK integration rather than the JWT mechanics themselves); self-hosted Keycloak/OIDC (would keep the self-hosted rule but was a step past what's needed for a single-admin app - revisit only if multi-admin/real IdP integration becomes an actual goal).
  - Viewer/Display stay unauthenticated by design (room UUID is the only gate) - this auth work is scoped to admin-only endpoints/dashboard.

## Infrastructure

- Self-hosted, Docker-based stack, deployed on the user's own **Hostinger VPS**.
- Explicitly rejected for the core system: managed SaaS - no Supabase (considered, passed on), no Ably/Pusher/PartyKit managed realtime.
- Standing philosophy for this project: **"everything I can install should be our default"** - prefer installable/self-hosted open-source components over managed cloud services throughout.

## Message bus (Kafka / NATS / Redpanda-style)

- **Deferred to phase 2.** MVP ships with in-memory room state in a single FastAPI process handling WebSocket fanout directly - no bus.
- Once the MVP loop (sync + reactions) works end to end, a message bus goes in deliberately as a hands-on **learning exercise** - not because v1 hits a scaling wall it needs solving. This is a stated goal, not a technical requirement of the MVP.

## Open questions (frontier not yet settled)

- Reaction rendering: exact visual treatment (float-up/burst/particle animation) and rendering tech (Canvas/WebGL/CSS/Svelte transitions) for the Display screen.
- Persistence schema detail: exact tables/fields for rooms, decks, check-ins/participants, reaction history, metrics (headline decided - everything persists - schema itself isn't).
- Room/deck relationship: is a deck tied 1:1 to a room forever, or can one saved deck be reused to spin up multiple room instances for repeat deliveries of the same talk?
