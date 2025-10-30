<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { authStore } from '$lib/stores/auth';
  import { api } from '$lib/api';
  import SignOutButton from '$lib/components/SignOutButton.svelte';

  let loading = true;
  let resultStatus = '';
  let matchStatus = '';
  let userEmail = '';
  let matchedUserName = '';
  let matchedUserEmail = '';
  let matchedUserPhoneNumber = '';
  let showModal = false;
  let round2Applied = false;
  let thankyouMessage = '';

  onMount(async () => {
    await authStore.loadSession();
    const session = await new Promise(resolve => {
      const unsub = authStore.subscribe(v => { resolve(v); unsub(); });
    });
    if (!session?.authenticated) return goto('/');
    userEmail = session.user.email;

    try {
      const res = await api.round1.checkResult(userEmail);
      resultStatus = res.status;
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
      await api.round1.updateMatchStatus(userEmail, apply);
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
</script>

{#if loading}
  <div class="center"><p>Checking your results...</p></div>
{:else if resultStatus === 'not_published'}
  <div class="center"><p>Results not published yet.</p></div>
{:else if resultStatus === 'not_registered'}
  <div class="center"><p>Please proceed with your round 2 registration.</p></div>
{:else if resultStatus === 'no_match'}
  <div class="center"><p>No match found. You’re automatically enrolled in Round 2!</p></div>
{:else if resultStatus === 'match_found'}
  <div class="center">
    <div class="signout"><SignOutButton /></div>
    <h2>We found your match!</h2>
    <p><b>{matchedUserName}</b></p>
    <p>{matchedUserEmail}</p>
    <p>{matchedUserPhoneNumber}</p>

    {#if matchStatus !== 'DECLINED'}
      <button class="decline" on:click={() => showModal = true}>Decline Match</button>
    {/if}
  </div>
{/if}

{#if thankyouMessage}
  <div class="center"><p>{thankyouMessage}</p></div>
{:else if round2Applied}
  <div class="center"><p>We might have a Round 2! You’ll be automatically enrolled.</p></div>
{/if}

{#if showModal}
  <div class="modal-overlay" on:click={() => showModal = false}>
    <div class="modal-content" on:click={(e) => e.stopPropagation()}>
      <h2>Would you like to be considered for Round 2?</h2>
      <p>You can choose to be matched with someone new in Round 2, or opt out completely.</p>
      <div class="buttons">
        <button on:click={() => handleRound2Choice(false)}>No Round 2</button>
        <button on:click={() => handleRound2Choice(true)}>Apply Round 2</button>
      </div>
    </div>
  </div>
{/if}

<style>
  .center {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100vh;
    font-family: 'Nunito', sans-serif;
    color: #333;
    text-align: center;
    background-color: white;
  }

  .signout {
    position: absolute;
    top: 1rem;
    right: 1rem;
  }

  h2 {
    color: var(--primary-color);
    margin-bottom: 1rem;
  }

  p {
    margin: 0.5rem 0;
  }

  .decline {
    margin-top: 1rem;
    padding: 0.75rem 1.5rem;
    border: none;
    border-radius: 25px;
    background-color: var(--primary-color);
    color: white;
    font-weight: bold;
    cursor: pointer;
  }

  .modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.7);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }

  .modal-content {
    background-color: white;
    padding: 2rem;
    border-radius: 1rem;
    max-width: 500px;
    width: 90%;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    text-align: center;
  }

  .buttons {
    display: flex;
    justify-content: center;
    gap: 1rem;
    margin-top: 1.5rem;
  }

  .buttons button {
    padding: 0.75rem 1.25rem;
    border: none;
    border-radius: 25px;
    color: white;
    cursor: pointer;
    font-weight: bold;
  }

  .buttons button:first-child {
    background-color: #999;
  }

  .buttons button:last-child {
    background-color: var(--primary-color);
  }

  .buttons button:hover {
    filter: brightness(1.1);
    transform: scale(1.05);
  }
</style>