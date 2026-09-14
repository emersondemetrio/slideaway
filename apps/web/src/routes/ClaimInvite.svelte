<script>
  import { push } from "svelte-spa-router";
  import { apiFetch } from "../lib/api.js";
  import { setTokens } from "../lib/auth.js";

  let { params } = $props();
  const token = $derived(params.token);

  let email = $state("");
  let password = $state("");
  let error = $state("");

  async function handleSubmit(event) {
    event.preventDefault();
    error = "";
    try {
      const data = await apiFetch("/auth/invites/claim", {
        method: "POST",
        body: JSON.stringify({ token, email, password }),
      });
      setTokens(data.access_token, data.refresh_token);
      push("/dashboard");
    } catch (err) {
      error = err.message;
    }
  }
</script>

<main>
  <h1>Claim your Slideaway account</h1>
  <form onsubmit={handleSubmit}>
    <label>
      Email
      <input type="email" bind:value={email} required />
    </label>
    <label>
      Password
      <input type="password" bind:value={password} required />
    </label>
    <button type="submit">Create account</button>
    {#if error}
      <p class="error">{error}</p>
    {/if}
  </form>
</main>

<style>
  main {
    max-width: 320px;
    margin: 4rem auto;
    font-family: system-ui, sans-serif;
  }
  form {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }
  .error {
    color: #c0392b;
  }
</style>
