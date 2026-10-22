<script lang="ts">
  import { onMount } from 'svelte';
  import { get } from 'svelte/store';
  import { goto } from '$app/navigation';
  import { authStore } from '$lib/stores/auth';
  import { configStore } from '$lib/stores/config';
  import { api } from '$lib/api';
  import { fade, scale } from 'svelte/transition';
  import { cubicOut } from 'svelte/easing';
  import SignOutButton from '$lib/components/SignOutButton.svelte';
  import LoadingScreen from '$lib/components/LoadingScreen.svelte';
  import FloatingHearts from '$lib/components/FloatingHearts.svelte';
  import { fadeIn } from '$lib/actions/fadeIn';

  let loading = $state(true);
  let resultStatus = $state('');
  let matchStatus = $state('');
  let userEmail = $state('');
  let matchedUserName = $state('');
  let matchedUserEmail = $state('');
  let matchedUserPhoneNumber = $state('');
  let showModal = $state(false);
  let round2Applied = $state(false);
  let thankyouMessage = $state('');

  onMount(async () => {
    await authStore.loadSession();
    const session = get(authStore);
    if (!session?.authenticated) return goto('/');
    userEmail = session.user?.email ?? '';

    try {
      const res = await api.round1.checkResult();
      resultStatus = res.status;
      if (resultStatus === 'not_registered' && !get(configStore).registrationsClosed) {
        goto('/userForm');
        return;
      }
      matchStatus = res.match_status;
      if (res.match) {
        matchedUserName = res.match.name;
        matchedUserEmail = res.match.email;
        matchedUserPhoneNumber = res.match.phone;
      }
    } catch (e) {
      console.error(e);
    } finally {
      loading = false;
    }
  });

  async function handleRound2Choice(apply: boolean) {
    try {
      await api.round1.updateMatchStatus(apply);
      showModal = false;
      if (apply) {
        round2Applied = true;
      } else {
        thankyouMessage = 'Thank you for registering. Hope you had a good experience!';
      }
      location.reload();
    } catch (error) {
      console.error('Error updating match status:', error);
      alert('Failed to update your choice. Please try again.');
    }
  }

  function closeModal() {
    showModal = false;
  }
</script>

<svelte:head>
  <link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap" rel="stylesheet" />
</svelte:head>

<svelte:window onkeydown={(e) => { if (showModal && e.key === 'Escape') closeModal(); }} />

{#if loading}
  <LoadingScreen message="Checking your results..." />
{:else}
<main class="end-screen min-h-dvh flex items-center justify-center px-4 py-16 sm:py-12" style="background-color: var(--primary-color);">
  {#if resultStatus === 'match_found'}
    <FloatingHearts />
  {/if}

  <div class="absolute top-4 right-4 z-50"><SignOutButton /></div>

  <div class="relative z-10 w-full max-w-4xl flex flex-col lg:flex-row items-center justify-center gap-6 lg:gap-16">
    <img
      src="/images/logo.webp"
      alt="Find Your Date"
      width="900"
      height="900"
      use:fadeIn
      class="w-40 sm:w-48 lg:w-72 h-auto drop-shadow-lg shrink-0"
    />

    <div class="w-full max-w-md flex flex-col gap-4">
    <section class="card w-full max-w-md bg-white rounded-3xl shadow-2xl px-6 py-8 sm:px-10 sm:py-10 text-center" in:scale={{ start: 0.96, duration: 400, easing: cubicOut }}>
      {#if thankyouMessage}
        <p class="status-text">{thankyouMessage}</p>
      {:else if round2Applied}
        <p class="status-text">We might have a Round 2! You’ll be automatically enrolled.</p>
      {:else if resultStatus === 'not_published'}
        <div class="emoji" aria-hidden="true">⏳</div>
        <h1>Results coming soon</h1>
        <p class="status-text">You're in! We're finding your match, so check back soon.</p>
      {:else if resultStatus === 'waiting_for_results'}
        <div class="emoji" aria-hidden="true">💌</div>
        <h1>Hang tight!</h1>
        <p class="status-text">Waiting for Round 2 results...</p>
      {:else if resultStatus === 'not_registered'}
        <div class="emoji" aria-hidden="true">💕</div>
        <h1>Registrations are closed</h1>
        <p class="status-text">Sorry, sign-ups have ended and you didn't finish registering in time. Thanks for your interest!</p>
      {:else if resultStatus === 'no_match'}
        <div class="emoji" aria-hidden="true">💞</div>
        <h1>No match this time</h1>
        <p class="status-text">Sorry, we couldn't find you a match this time. Thanks for taking part!</p>
      {:else if resultStatus === 'match_found' && matchStatus === 'partner_declined'}
        <div class="emoji" aria-hidden="true">🌷</div>
        <h1>Your match can't make it</h1>
        <p class="status-text">Your match won't be able to join you this time. It's nothing to do with you, and we're sorry it didn't work out. Thanks so much for being part of FindYourDate!</p>
      {:else if resultStatus === 'match_found'}
        <div class="emoji" aria-hidden="true">💘</div>
        <h1>{matchStatus === 'rejected' ? 'Match declined' : 'We found your match!'}</h1>
        <div class="match-details">
          <p class="match-name">{matchedUserName}</p>
          {#if matchedUserEmail}
            <a href="mailto:{matchedUserEmail}" class="match-contact">{matchedUserEmail}</a>
          {/if}
          {#if matchedUserPhoneNumber}
            <a href="tel:{matchedUserPhoneNumber}" class="match-contact match-phone">{matchedUserPhoneNumber}</a>
          {/if}
        </div>

        {#if matchStatus === 'rejected'}
          <p class="status-text mt-6">You've declined this match.</p>
        {:else}
          <button class="btn btn-ghost mt-6" onclick={() => showModal = true}>Decline Match</button>
        {/if}
      {:else}
        <div class="emoji" aria-hidden="true">🙈</div>
        <p class="status-text">We couldn't load your results right now. Please refresh in a moment.</p>
      {/if}
    </section>

    <!-- Plug for another club event; drop this block once it's over -->
    <a
      class="promo"
      href="https://docs.google.com/forms/d/e/1FAIpQLSc54ADCvEpYBTbCVPSFSlBkKrQbEIrZ0LFvOpfc-wDY8RoAOg/viewform"
      target="_blank"
      rel="noopener noreferrer"
    >
      <span class="promo-tag">Also from GDG</span>
      <span class="promo-title">Labyrinth</span>
      <span class="promo-text">Dare to crack it? Come along and find out.</span>
      <span class="promo-meta">25 OCT · 3–4 PM<br />PRIZE POOL ₹2K</span>
      <span class="promo-cta">Register now</span>
    </a>
    </div>
  </div>
</main>
{/if}

{#if showModal}
  <div class="modal-overlay" transition:fade={{ duration: 200 }}>
    <button class="modal-backdrop" aria-label="Close" tabindex="-1" onclick={closeModal}></button>
    <div
      class="modal-content"
      role="dialog"
      aria-modal="true"
      aria-labelledby="decline-title"
      transition:scale={{ start: 0.94, duration: 250, easing: cubicOut }}
    >
      <h2 id="decline-title">Decline this match?</h2>
      <p>You won't be matched with anyone else.</p>
      <div class="buttons">
        <button class="btn btn-muted" onclick={closeModal}>Cancel</button>
        <button class="btn btn-primary" onclick={() => handleRound2Choice(false)}>Decline</button>
      </div>
    </div>
  </div>
{/if}

<style>
  .end-screen {
    position: relative;
    overflow: hidden;
  }

  .emoji {
    font-size: 3rem;
    line-height: 1;
    margin-bottom: 1rem;
  }

  h1 {
    font-size: 1.75rem;
    font-weight: 800;
    color: var(--secondary-color);
    margin-bottom: 0.5rem;
    text-wrap: balance;
  }

  .status-text {
    font-size: 1.05rem;
    font-weight: 600;
    color: var(--secondary-color);
    opacity: 0.85;
    text-wrap: balance;
  }

  /* Labyrinth plug: 8-bit arcade look, square corners and stepped pixel shadows */
  .promo {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.6rem;
    padding: 1.25rem 1rem 1.4rem;
    background-color: #1b1240;
    background-image:
      linear-gradient(rgba(255, 255, 255, 0.04) 1px, transparent 1px),
      linear-gradient(90deg, rgba(255, 255, 255, 0.04) 1px, transparent 1px);
    background-size: 8px 8px;
    border: 4px solid #00e5ff;
    box-shadow: 6px 6px 0 #ff3e9a, 12px 12px 0 rgba(0, 0, 0, 0.25);
    text-align: center;
    text-decoration: none;
    image-rendering: pixelated;
    transition: transform 0.1s steps(2);
  }
  .promo:hover { transform: translate(-2px, -2px); }
  .promo:active { transform: translate(3px, 3px); box-shadow: 3px 3px 0 #ff3e9a; }
  .promo-tag, .promo-title, .promo-meta, .promo-cta {
    font-family: 'Press Start 2P', monospace;
  }
  .promo-tag {
    font-size: 0.55rem;
    color: #7dffb0;
    letter-spacing: 0.1em;
  }
  .promo-title {
    font-size: 1.35rem;
    line-height: 1.3;
    color: #ffd23f;
    text-shadow: 3px 3px 0 #ff3e9a;
  }
  .promo-text {
    font-size: 0.9rem;
    font-weight: 600;
    color: #e8e4ff;
  }
  .promo-meta {
    font-size: 0.55rem;
    line-height: 1.8;
    color: #00e5ff;
  }
  .promo-cta {
    margin-top: 0.4rem;
    padding: 0.7rem 1rem;
    font-size: 0.65rem;
    background-color: #ff3e9a;
    color: #fff;
    box-shadow: 4px 4px 0 #ffd23f;
  }
  .promo-cta::after { content: ' ▶'; }

  .match-details {
    margin-top: 1.25rem;
    padding: 1.25rem;
    border-radius: 1.25rem;
    background-color: rgba(236, 167, 186, 0.15);
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
  }

  .match-name {
    font-size: 1.35rem;
    font-weight: 800;
    color: var(--accent-color);
    overflow-wrap: anywhere;
  }

  .match-contact {
    font-weight: 600;
    color: var(--secondary-color);
    overflow-wrap: anywhere;
    text-decoration: none;
  }

  .match-phone {
    font-size: 1.35rem;
    font-weight: 800;
    letter-spacing: 0.04em;
  }

  .match-contact:hover {
    text-decoration: underline;
  }

  .btn {
    padding: 0.75rem 1.5rem;
    border: none;
    border-radius: 9999px;
    font-weight: 600;
    transition: transform 0.2s var(--ease-out), filter 0.2s, background-color 0.2s;
  }

  .btn:hover {
    filter: brightness(1.05);
    transform: translateY(-1px) scale(1.03);
  }

  .btn:active {
    transform: scale(0.97);
  }

  .btn-primary {
    background-color: var(--secondary-color);
    color: white;
  }

  .btn-muted {
    background-color: #999;
    color: white;
  }

  .btn-ghost {
    background-color: transparent;
    color: var(--secondary-color);
    border: 2px solid var(--primary-color);
  }

  .btn-ghost:hover {
    background-color: var(--primary-color);
    color: white;
  }

  .modal-overlay {
    position: fixed;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 1rem;
    z-index: 1000;
  }

  .modal-backdrop {
    position: absolute;
    inset: 0;
    border: none;
    background-color: rgba(49, 48, 53, 0.6);
    backdrop-filter: blur(4px);
    -webkit-backdrop-filter: blur(4px);
    cursor: default;
  }

  .modal-content {
    position: relative;
    background-color: white;
    padding: 2rem;
    border-radius: 1.5rem;
    max-width: 500px;
    width: 100%;
    box-shadow: 0 30px 60px -20px rgba(0, 0, 0, 0.4);
    text-align: center;
    color: var(--secondary-color);
  }

  .modal-content h2 {
    font-size: 1.35rem;
    font-weight: 800;
    color: var(--secondary-color);
    margin-bottom: 0.75rem;
    text-wrap: balance;
  }

  .buttons {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 0.75rem;
    margin-top: 1.5rem;
  }
</style>
