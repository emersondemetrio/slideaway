# Svelte / Frontend Review Reference

Condensed from [spences10/svelte-skills-kit](https://github.com/spences10/svelte-skills-kit) (svelte-runes/references/common-mistakes.md, MIT-licensed) and general frontend review practice. Svelte 5 runes only - do not apply Svelte 4 (`$:`, `on:`, `export let`) expectations to Svelte 5 code, and vice versa.

## Reactivity (highest-value checks)

- `$effect` used to compute a value instead of `$derived`. Anything of the shape `$effect(() => { x = f(y) })` where `x` is never used for a real side effect (DOM manipulation, logging, a network call) is almost always supposed to be `$derived`.
- `$effect` used to sync two pieces of state to each other (two effects each assigning into the other's dependency) - fragile, prefer a single source of truth updated via an event handler.
- A value read through optional chaining inside `$effect` (`a?.b(c)`) where `a` is sometimes nullish - if `a` is nullish, `c` is never read, so the effect does not depend on `c` and will not re-run when `c` changes.
- An `$effect` that both reads and writes the same piece of state it depends on - infinite loop risk.
- A rune (`$state`, `$derived`, `$props`, etc.) declared inside a function or non-top-level block instead of at component top level - not valid, must be at the top level or inside a class field.
- A plain `let` for a value that changes and is expected to update the UI - Svelte 5 has no implicit reactivity; missing `$state()` means the UI silently never updates.
- Mixing Svelte 4 and Svelte 5 syntax in the same component (`$:` reactive statements alongside runes, or `on:click` alongside `onclick`).
- A prop destructured from `$props()` that the component expects to receive two-way binding on, without `$bindable()`.
- `{children}` rendered directly instead of `{@render children()}` - renders `[object Object]` instead of content.
- A route/page component that destructures a reactive prop (e.g. router params) into a plain `const` instead of `$derived(...)` - the value is captured once and never updates if the same component instance is reused for a new route/param. This is a real, previously-hit bug in this repo (see `apps/web/src/routes/Viewer.svelte`, `Display.svelte`, `ClaimInvite.svelte`).

## Performance

- `$state()` wrapping a value that never changes (should be a plain `const`).
- `$derived()` used for a value only read once and not reused - inlining is simpler and equally correct.
- `$state()` wrapping a large, effectively-immutable object where deep-proxy overhead isn't needed - consider `$state.raw()`.

## General frontend / UI

- Components exceeding roughly 200-300 lines - a signal to split into smaller components, not an automatic failure.
- CSS: overly specific selectors, `!important`, inline styles, animating `top`/`left`/`width`/`height` instead of `transform` - all worth flagging, especially in animation-heavy code (this app's reaction bursts are a real risk area for this).
- Any place user-controlled data reaches the DOM through something other than Svelte's default text interpolation (e.g. `{@html ...}`) - Svelte auto-escapes by default, so `{@html}` on unsanitized input is a real XSS vector, not a theoretical one.
- Accessibility basics on interactive elements: a `<button>` (not a `<div onclick>`), form inputs paired with a `<label>` (this repo's Login/ClaimInvite forms already do this correctly via `bind:value` + `<label>`, worth checking new forms follow the same pattern).
- Fetch/socket error handling: does a failed `apiFetch` call actually surface to the user (an `error` state shown in the template), or does it silently swallow the rejection?
