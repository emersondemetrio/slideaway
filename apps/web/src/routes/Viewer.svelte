<script>
  import { onDestroy, onMount } from "svelte";
  import { apiFetch } from "../lib/api.js";
  import { joinRoom, leaveRoom, onPresentationEnded, onReaction, onSlideChanged } from "../lib/socket.js";

  let { params } = $props();
  const roomId = $derived(params.roomId);

  const REACTIONS = ["like", "love", "haha", "yay", "wow", "sad", "angry"];
  const REACTION_EMOJI = {
    like: "👍",
    love: "❤️",
    haha: "😆",
    yay: "☺️",
    wow: "😮",
    sad: "😢",
    angry: "😠",
  };

  let participantId = $state(null);
  let liveSlideIndex = $state(0);
  let viewedSlideIndex = $state(0);
  let ended = $state(false);
  let tallies = $state(Object.fromEntries(REACTIONS.map((r) => [r, 0])));

  const isDrifted = $derived(viewedSlideIndex !== liveSlideIndex);

  onMount(async () => {
    const data = await apiFetch(`/rooms/${roomId}/checkin`, {
      method: "POST",
      body: JSON.stringify({ user_agent: navigator.userAgent }),
    });
    participantId = data.participant_id;
    liveSlideIndex = data.room.current_slide_index;
    viewedSlideIndex = liveSlideIndex;

    joinRoom(roomId);

    onSlideChanged((event) => {
      if (event.room_id !== roomId) return;
      if (viewedSlideIndex === liveSlideIndex) {
        viewedSlideIndex = event.slide_index;
      }
      liveSlideIndex = event.slide_index;
    });

    onPresentationEnded((event) => {
      if (event.room_id === roomId) ended = true;
    });

    onReaction((event) => {
      if (event.room_id === roomId) tallies[event.emoji_type] += 1;
    });
  });

  onDestroy(() => leaveRoom(roomId));

  function goBack() {
    if (viewedSlideIndex > 0) viewedSlideIndex -= 1;
  }

  function jumpToLive() {
    viewedSlideIndex = liveSlideIndex;
  }

  async function react(emojiType) {
    await apiFetch(`/rooms/${roomId}/react`, {
      method: "POST",
      body: JSON.stringify({ participant_id: participantId, emoji_type: emojiType }),
    });
  }
</script>

<main>
  {#if ended}
    <p class="ended">This presentation has ended.</p>
  {:else}
    {#if isDrifted}
      <button class="live-indicator" onclick={jumpToLive}>🟢 back to live</button>
    {/if}

    <section class="slide">
      <h2>Slide {viewedSlideIndex + 1}</h2>
    </section>

    <button onclick={goBack} disabled={viewedSlideIndex === 0}>⬅ back</button>

    <section class="reactions">
      {#each REACTIONS as emojiType}
        <button onclick={() => react(emojiType)}>{REACTION_EMOJI[emojiType]}</button>
      {/each}
    </section>
  {/if}
</main>

<style>
  main {
    max-width: 480px;
    margin: 0 auto;
    padding: 1rem;
    font-family: system-ui, sans-serif;
    text-align: center;
  }
  .live-indicator {
    position: fixed;
    top: 1rem;
    right: 1rem;
    animation: blink 1.2s infinite;
  }
  @keyframes blink {
    50% {
      opacity: 0.3;
    }
  }
  .reactions {
    display: flex;
    justify-content: center;
    gap: 0.5rem;
    margin-top: 1.5rem;
    font-size: 1.5rem;
  }
  .ended {
    font-size: 1.25rem;
    margin-top: 4rem;
  }
</style>
