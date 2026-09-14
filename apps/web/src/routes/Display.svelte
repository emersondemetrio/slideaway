<script>
  import { onDestroy, onMount } from "svelte";
  import { fly } from "svelte/transition";
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

  let slideIndex = $state(0);
  let ended = $state(false);
  let tallies = $state(Object.fromEntries(REACTIONS.map((r) => [r, 0])));
  let bursts = $state([]);
  let burstId = 0;

  onMount(() => {
    joinRoom(roomId);

    onSlideChanged((event) => {
      if (event.room_id === roomId) slideIndex = event.slide_index;
    });

    onPresentationEnded((event) => {
      if (event.room_id === roomId) ended = true;
    });

    onReaction((event) => {
      if (event.room_id !== roomId) return;
      tallies[event.emoji_type] += 1;

      const id = burstId++;
      bursts = [...bursts, { id, emojiType: event.emoji_type, left: Math.random() * 80 + 10 }];
      setTimeout(() => {
        bursts = bursts.filter((b) => b.id !== id);
      }, 2000);
    });
  });

  onDestroy(() => leaveRoom(roomId));
</script>

<main>
  {#if ended}
    <p class="ended">Thanks for joining!</p>
  {:else}
    <section class="slide">
      <h1>Slide {slideIndex + 1}</h1>
    </section>

    <section class="tallies">
      {#each REACTIONS as emojiType}
        <span>{REACTION_EMOJI[emojiType]} {tallies[emojiType]}</span>
      {/each}
    </section>

    <div class="burst-layer">
      {#each bursts as burst (burst.id)}
        <span
          class="burst"
          style="left: {burst.left}%"
          in:fly={{ y: 0, duration: 200 }}
          out:fly={{ y: -300, duration: 1800 }}
        >
          {REACTION_EMOJI[burst.emojiType]}
        </span>
      {/each}
    </div>
  {/if}
</main>

<style>
  main {
    position: relative;
    height: 100vh;
    font-family: system-ui, sans-serif;
    text-align: center;
    overflow: hidden;
  }
  .slide {
    padding-top: 8vh;
    font-size: 3rem;
  }
  .tallies {
    position: fixed;
    bottom: 1.5rem;
    left: 50%;
    transform: translateX(-50%);
    display: flex;
    gap: 1.5rem;
    font-size: 1.5rem;
  }
  .burst-layer {
    position: fixed;
    inset: 0;
    pointer-events: none;
  }
  .burst {
    position: absolute;
    bottom: 10vh;
    font-size: 2.5rem;
  }
  .ended {
    font-size: 2rem;
    margin-top: 40vh;
  }
</style>
