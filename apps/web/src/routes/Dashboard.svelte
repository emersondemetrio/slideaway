<script>
  import { onMount } from "svelte";
  import { push } from "svelte-spa-router";
  import { apiFetch } from "../lib/api.js";
  import { clearTokens, getRole, hasRole, isAuthenticated } from "../lib/auth.js";

  let decks = $state([]);
  let roomLinks = $state({});
  let inviteLink = $state("");
  let error = $state("");

  const isSuperAdmin = hasRole("super_admin");

  onMount(async () => {
    if (!isAuthenticated()) {
      push("/login");
      return;
    }
    decks = await apiFetch("/decks");
  });

  async function createRoom(series) {
    const latest = series.versions.at(-1);
    try {
      const room = await apiFetch(`/decks/${latest.id}/rooms`, { method: "POST" });
      roomLinks = {
        ...roomLinks,
        [series.id]: {
          viewer: `${window.location.origin}/#/rooms/${room.id}/viewer`,
          display: `${window.location.origin}/#/rooms/${room.id}/display`,
        },
      };
    } catch (err) {
      error = err.message;
    }
  }

  async function createInvite() {
    try {
      const invite = await apiFetch("/auth/invites", {
        method: "POST",
        body: JSON.stringify({ role_to_grant: "user", expires_in_days: 7 }),
      });
      inviteLink = `${window.location.origin}/#/claim-invite/${invite.token}`;
    } catch (err) {
      error = err.message;
    }
  }

  function logout() {
    clearTokens();
    push("/login");
  }
</script>

<main>
  <header>
    <h1>Dashboard</h1>
    <p>Role: {getRole()}</p>
    <button onclick={logout}>Log out</button>
  </header>

  {#if error}
    <p class="error">{error}</p>
  {/if}

  <section>
    <h2>Your decks</h2>
    {#each decks as series}
      <article>
        <h3>{series.title}</h3>
        <button onclick={() => createRoom(series)}>Start / resume room</button>
        {#if roomLinks[series.id]}
          <p><a href={roomLinks[series.id].viewer}>Viewer link</a></p>
          <p><a href={roomLinks[series.id].display}>Display link</a></p>
        {/if}
      </article>
    {/each}
  </section>

  {#if isSuperAdmin}
    <section>
      <h2>Invite a user (super-admin)</h2>
      <button onclick={createInvite}>Generate invite link</button>
      {#if inviteLink}
        <p>{inviteLink}</p>
      {/if}
    </section>
  {/if}
</main>

<style>
  main {
    max-width: 640px;
    margin: 2rem auto;
    font-family: system-ui, sans-serif;
  }
  .error {
    color: #c0392b;
  }
  article {
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 1rem;
  }
</style>
