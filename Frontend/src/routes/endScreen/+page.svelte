<script>
    import * as rive from "@rive-app/canvas";
    import { onMount } from 'svelte';
    import { goto } from '$app/navigation';
    import { authStore } from '$lib/stores/auth';
    import { API_BASE_URL } from '$lib/api';
    import SignOutButton from '$lib/components/SignOutButton.svelte';

    let canvas;
    let currentAnimation = '';
    let currentText = $state('');
    let showDots = $state(false);
    let showButton = $state(false);
    let riveInstance = null;
    let matchRevealed = $state(false);
    let hearts = $state([]);
    let heartInterval = null;
    let displayedName = $state('');
    let showAge = $state(false);
    let loading = $state(true);
    
    // TODO: Replace with actual matched user data from your backend/state
    let matchedUserName = 'Sarah';
    let matchedUserAge = 24;

    function createHeart() {
      const heart = {
        id: Math.random(),
        left: Math.random() * 100, // Random position from 0-100%
        duration: 3 + Math.random() * 2, // Random duration between 3-5s
        delay: Math.random() * 0.5, // Random delay between 0-0.5s
        size: 50 + Math.random() * 50, // Random size between 50-100px
        rotation: -45 + Math.random() * 90 // Random rotation between -45 and 45 degrees
      };
      hearts = [...hearts, heart];
      
      // Remove heart after animation completes
      setTimeout(() => {
        hearts = hearts.filter(h => h.id !== heart.id);
      }, (heart.duration + heart.delay) * 1000);
    }

    function startHeartAnimation() {
      // Create initial batch of hearts
      for (let i = 0; i < 2; i++) {
        setTimeout(() => createHeart(), i * 200);
      }
      
      // Continue creating hearts at random intervals
      heartInterval = setInterval(() => {
        createHeart();
      }, 800); // Create a new heart every 800ms
    }

    function stopHeartAnimation() {
      if (heartInterval) {
        clearInterval(heartInterval);
        heartInterval = null;
      }
      hearts = [];
    }

    function typewriterEffect() {
      displayedName = '';
      showAge = false;
      let index = 0;
      
      const typingInterval = setInterval(() => {
        if (index < matchedUserName.length) {
          displayedName += matchedUserName[index];
          index++;
        } else {
          clearInterval(typingInterval);
          // Show age after name is fully typed
          setTimeout(() => {
            showAge = true;
          }, 300);
        }
      }, 400); // Type one character every 200ms
    }

    function playAnalyzingAnimation() {
      currentAnimation = '/animations/heart-hi.riv';
      currentText = 'Finding your perfect match';
      showDots = true;
      showButton = false;
      loadAnimation();
    }

    function playMatchFoundAnimation() {
      currentAnimation = '/animations/heart-happy.riv';
      currentText = 'WE HAVE FOUND YOU A MATCH!';
      showDots = false;
      showButton = true;
      loadAnimation();
    }

    function handleRevealMatch() {
      // Hide all contents and reveal match information
      matchRevealed = true;
      
      // Cleanup animation when revealing match
      if (riveInstance) {
        riveInstance.cleanup();
      }
      
      // Start heart animation
      startHeartAnimation();
      
      // Start typewriter effect
      typewriterEffect();
    }

    function loadAnimation() {
      if (!canvas) return;

      // Cleanup existing instance if any
      if (riveInstance) {
        riveInstance.cleanup();
      }

      // Create new instance with current animation
      riveInstance = new rive.Rive({
        src: currentAnimation,
        canvas: canvas,
        autoplay: true,
        onLoad: () => {
          riveInstance.resizeDrawingSurfaceToCanvas();
        }
      });
    }

    onMount(async () => {
        await authStore.loadSession();
        const currentSession = await new Promise(resolve => {
            const unsubscribe = authStore.subscribe(value => {
                resolve(value);
                unsubscribe();
            });
        });
        
        if (!currentSession?.authenticated) {
            goto('/');
            return;
        }

        // Check user status - only show endScreen if they've completed everything
        try {
            const response = await fetch(`${API_BASE_URL}/status/user-status?email=${encodeURIComponent(currentSession.user.email)}`, {
                credentials: 'include'
            });

            if (response.ok) {
                const data = await response.json();
                
                if (data.redirect_to === 'form') {
                    // User hasn't completed form yet
                    goto('/userForm');
                    return;
                } else if (data.redirect_to === 'chat') {
                    // User hasn't completed chat yet
                    sessionStorage.setItem('user_id', data.user_id);
                    goto('/aiChatRoom');
                    return;
                }
                // If redirect_to === 'complete', stay on this page
                sessionStorage.setItem('user_id', data.user_id);
            }
        } catch (error) {
            console.error('Error checking user status:', error);
        }
        
        // All checks passed, show the page
        loading = false;
        
        // Wait for DOM to render, then start animation
        setTimeout(() => {
            playAnalyzingAnimation();
        }, 200);
    });

    $effect(() => {
      return () => {
        if (riveInstance) {
          riveInstance.cleanup();
        }
        stopHeartAnimation();
      }
    });
</script>

{#if loading}
    <div class="bg-white flex items-center justify-center w-screen h-screen">
        <div class="text-center">
            <div class="w-16 h-16 border-4 border-t-transparent rounded-full animate-spin mx-auto mb-4" style="border-color: var(--primary-color); border-top-color: transparent;"></div>
            <p class="text-xl font-semibold" style="color: var(--primary-color); font-family: 'Nunito', sans-serif;">
                Loading your match...
            </p>
        </div>
    </div>
{:else}

<div class="bg-white flex justify-center items-center w-screen h-screen overflow-hidden relative">
  <!-- Sign Out Button - Top Right -->
  <div class="absolute top-4 right-4 z-50">
    <SignOutButton />
  </div>

  <!-- Floating hearts container (behind everything) -->
  {#if matchRevealed}
    <div class="hearts-container">
      {#each hearts as heart (heart.id)}
        <img 
          src="/images/pink-heart.png" 
          alt="heart"
          class="floating-heart"
          style="
            left: {heart.left}%;
            animation-duration: {heart.duration}s;
            animation-delay: {heart.delay}s;
            width: {heart.size}px;
            height: {heart.size}px;
            transform: rotate({heart.rotation}deg);
          "
        />
      {/each}
    </div>
  {/if}

  {#if matchRevealed}
    <div class="flex flex-col items-center justify-center gap-4 text-center px-4 relative z-10">
      <p class="text-3xl font-semibold" style="color: var(--secondary-color); font-family: 'Nunito', sans-serif;">
        You've been matched with
      </p>
      <p class="text-7xl font-bold typewriter" style="color: var(--primary-color); font-family: 'Nunito', sans-serif;">
        {displayedName}<span class="cursor">|</span>
      </p>
      {#if showAge}
        <p class="text-3xl font-bold fade-in" style="color: var(--primary-color); font-family: 'Nunito', sans-serif;">
          {matchedUserAge} years old
        </p>
      {/if}
    </div>
  {:else}
    <div class="flex flex-col items-center justify-center gap-4 relative z-10">
      <canvas bind:this={canvas} class="w-[900px] h-[900px] max-w-[90vw] max-h-[75vh] object-contain shrink-0"></canvas>
      <div class="flex flex-col items-center gap-4 text-center px-4">
        {#if currentText}
          <p class="text-2xl font-semibold" style="color: var(--primary-color); font-family: 'Nunito', sans-serif;">
            {currentText}{#if showDots}<span class="dots"></span>{/if}
          </p>
          {#if showDots}
            <p class="text-sm opacity-70 mt-2" style="color: var(--secondary-color); font-family: 'Nunito', sans-serif;">
              It might take a day once registrations are done to get your match
            </p>
          {/if}
        {/if}
        {#if showButton}
          <button 
            onclick={handleRevealMatch}
            class="reveal-button px-8 py-4 rounded-full text-white text-xl font-bold cursor-pointer"
            style="font-family: 'Nunito', sans-serif; background-color: var(--primary-color);"
          >
            Reveal Match
          </button>
        {/if}
      </div>
    </div>
  {/if}
</div>
{/if}

<style>
  .hearts-container {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    overflow: hidden;
    pointer-events: none;
    z-index: 0;
  }

  .floating-heart {
    position: absolute;
    bottom: -100px;
    animation: floatUp linear forwards;
    opacity: 0;
  }

  @keyframes floatUp {
    0% {
      translate: 0 0;
      opacity: 1;
    }
    50% {
      opacity: 0.8;
    }
    100% {
      translate: 0 -120vh;
      opacity: 0;
    }
  }

  .typewriter {
    position: relative;
    display: inline-block;
  }

  .cursor {
    display: inline-block;
    animation: blink 0.7s infinite;
    margin-left: 2px;
  }

  @keyframes blink {
    0%, 50% {
      opacity: 1;
    }
    51%, 100% {
      opacity: 0;
    }
  }

  .fade-in {
    animation: fadeIn 0.8s ease-in forwards;
  }

  @keyframes fadeIn {
    0% {
      opacity: 0;
      transform: translateY(10px);
    }
    100% {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .dots::after {
    content: '';
    animation: dots 1.5s steps(4, end) infinite;
  }

  @keyframes dots {
    0%, 20% {
      content: '';
    }
    40% {
      content: '.';
    }
    60% {
      content: '..';
    }
    80%, 100% {
      content: '...';
    }
  }

  .reveal-button {
    animation: bounce 1s ease-in-out infinite;
    transition: all 0.3s ease;
  }

  .reveal-button:hover {
    animation: none;
    filter: brightness(1.1);
    transform: scale(1.02);
  }

  @keyframes bounce {
    0%, 100% {
      transform: translateY(0);
    }
    50% {
      transform: translateY(10px);
    }
  }

  @media (max-width: 550px) {
    canvas {
      height: 300px !important;
    }
  }
</style>