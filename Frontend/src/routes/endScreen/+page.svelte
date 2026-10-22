<script lang="ts">
  import { onMount } from 'svelte';
  import { get } from 'svelte/store';
  import { goto } from '$app/navigation';
  import { authStore } from '$lib/stores/auth';
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
      if (resultStatus === 'not_registered') {
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

    <section class="card w-full max-w-md bg-white rounded-3xl shadow-2xl px-6 py-8 sm:px-10 sm:py-10 text-center" in:scale={{ start: 0.96, duration: 400, easing: cubicOut }}>
      {#if thankyouMessage}
        <p class="status-text">{thankyouMessage}</p>
      {:else if round2Applied}
        <p class="status-text">We might have a Round 2! You’ll be automatically enrolled.</p>
      {:else if resultStatus === 'not_published'}
        <div class="emoji" aria-hidden="true">⏳</div>
        <h1>Results aren't out yet</h1>
        <p class="status-text">Results not published yet. They'll be out later today, so check back soon!</p>
      {:else if resultStatus === 'waiting_for_results'}
        <div class="emoji" aria-hidden="true">💌</div>
        <h1>Hang tight!</h1>
        <p class="status-text">Waiting for Round 2 results...</p>
      {:else if resultStatus === 'not_registered'}
        <p class="status-text">Please proceed with your round 2 registration.</p>
      {:else if resultStatus === 'no_match'}
        <div class="emoji" aria-hidden="true">💞</div>
        <h1>No match this time</h1>
        <p class="status-text">No match found. You’re automatically enrolled in Round 2!</p>
      {:else if resultStatus === 'match_found'}
        <div class="emoji" aria-hidden="true">💘</div>
        <h1>We found your match!</h1>
        <div class="match-details">
          <p class="match-name">{matchedUserName}</p>
          {#if matchedUserEmail}
            <a href="mailto:{matchedUserEmail}" class="match-contact">{matchedUserEmail}</a>
          {/if}
          {#if matchedUserPhoneNumber}
            <a href="tel:{matchedUserPhoneNumber}" class="match-contact">{matchedUserPhoneNumber}</a>
          {/if}
        </div>

        {#if matchStatus !== 'DECLINED'}
          <button class="btn btn-ghost mt-6" onclick={() => showModal = true}>Decline Match</button>
        {/if}
      {:else}
        <div class="emoji" aria-hidden="true">🙈</div>
        <p class="status-text">We couldn't load your results right now. Please refresh in a moment.</p>
      {/if}
    </section>
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
      aria-labelledby="round2-title"
      transition:scale={{ start: 0.94, duration: 250, easing: cubicOut }}
    >
      <h2 id="round2-title">Would you like to be considered for Round 2?</h2>
      <p>You can choose to be matched with someone new in Round 2, or opt out completely.</p>
      <div class="buttons">
        <button class="btn btn-muted" onclick={() => handleRound2Choice(false)}>No Round 2</button>
        <button class="btn btn-primary" onclick={() => handleRound2Choice(true)}>Apply Round 2</button>
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
    background-color: var(--primary-color);
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
