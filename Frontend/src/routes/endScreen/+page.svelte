<script lang="ts">
    import * as rive from "@rive-app/canvas";
    import { onMount } from 'svelte';
    import { goto } from '$app/navigation';
    import { authStore } from '$lib/stores/auth';
    import { configStore } from '$lib/stores/config';
    import { api, API_BASE_URL } from '$lib/api';
    import SignOutButton from '$lib/components/SignOutButton.svelte';

    let canvas: HTMLCanvasElement;
    let currentAnimation = '';
    let currentText = '';
    let showDots = false;
    let showButton = false;
    let riveInstance: any = null;
    let matchRevealed = false;
    let hearts: any[] = [];
    let heartInterval: any = null;
    let displayedName = '';
    let showAge = false;
    let showPhoneNumber = false;
    let showDeclineButton = false;
    let showModal = false;
    let loading = true;
    let resultStatus: 'checking' | 'not_registered' | 'match_found' | 'no_match' | 'not_published' = 'checking';
    let matchStatus: 'ACCEPTED' | 'PENDING' | 'DECLINED' | null = null;
    let round1ResultPublished = false;

    // Match data
    let matchedUserName = '';
    let matchedUserEmail = '';
    let matchedUserPhoneNumber = '';
    let userEmail = '';

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
      showPhoneNumber = false;
      let index = 0;

      const typingInterval = setInterval(() => {
        if (index < matchedUserName.length) {
          displayedName += matchedUserName[index];
          index++;
        } else {
          clearInterval(typingInterval);
          // Show phone number after name is fully typed
          setTimeout(() => {
            showPhoneNumber = true;
            // Show decline button after phone number is shown
            setTimeout(() => {
              showDeclineButton = true;
            }, 300);
          }, 500);
        }
      }, 100);
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
      resultStatus = 'match_found';
      // Animation will load via $effect when canvas is ready
    }

    function playSadAnimation() {
      currentAnimation = '/animations/heart-sleeping.riv';
      currentText = "No match found, but don't worry!";
      showDots = false;
      showButton = false;
      showDeclineButton = false;
      // Animation will load via $effect when canvas is ready
    }
    
    function playNotRegisteredAnimation() {
      currentAnimation = '/animations/heart-sleeping.riv';
      currentText = "You're not registered for Round 1";
      showDots = false;
      showButton = false;
      showDeclineButton = false;
      loadAnimation();
    }

    function handleRevealMatch() {
      console.log('Reveal Match clicked');
      if (!matchRevealed) {
        matchRevealed = true;
        if (riveInstance) {
            riveInstance.cleanup();
        }
        startHeartAnimation();
        typewriterEffect();
        console.log('Reveal match triggered');
      }
    }

    function handleDecline() {
      showModal = true;
    }
    
    async function handleRound2Choice(applyRound2: boolean) {
      try {
        await api.round1.updateMatchStatus(userEmail, applyRound2);
        showModal = false;
        
        // Show confirmation message
        if (applyRound2) {
          alert('You have been enrolled in Round 2!');
        } else {
          alert('You have opted out of Round 2.');
        }
      } catch (error) {
        console.error('Error updating match status:', error);
        alert('Failed to update your choice. Please try again.');
      }
    }

    function loadAnimation() {
      setTimeout(() => {
        if (!canvas) {
          console.error('Canvas element is not available.');
          return;
        }

        // Cleanup existing instance if any
        if (riveInstance) {
          riveInstance.cleanup();
        }

        // Create new instance with current animation
        try {
          riveInstance = new rive.Rive({
            src: currentAnimation,
            canvas: canvas,
            autoplay: true,
            onLoad: () => {
              console.log('Rive animation loaded successfully.');
              riveInstance.resizeDrawingSurfaceToCanvas();
              riveInstance.play();
            },
            onError: (error) => {
              console.error('Error loading Rive animation:', error);
              currentAnimation = '';
              currentText = "You're not registered for Round 1";
            }
          });
        } catch (error) {
          console.error('Failed to initialize Rive animation:', error);
        }
      }, 100); // Delay initialization by 100ms
    }

    onMount(async () => {
        // Check config first
        configStore.subscribe(config => {
            round1ResultPublished = config.round1ResultPublished;
        });
        
        await authStore.loadSession();
        interface AuthSession {
            authenticated: boolean;
            user: {
                email: string;
                // add other user properties if needed
            };
        }

        const currentSession = await new Promise<AuthSession>(resolve => {
            const unsubscribe = authStore.subscribe((value: AuthSession) => {
                resolve(value);
                unsubscribe();
            });
        });
        
        if (!currentSession?.authenticated) {
            goto('/');
            return;
        }
        
        userEmail = currentSession.user.email;

        // Check if Round 1 results are published
        if (!round1ResultPublished) {
            resultStatus = 'not_published';
            loading = false;
            return;
        }

        try {
            // Check Round 1 results
            const result = await api.round1.checkResult(userEmail);
            resultStatus = result.status;
            matchStatus = result.match_status || null;

            // Wait for canvas to mount before playing animation
            if (result.status === 'match_found') {
                matchedUserName = result.match.name;
                matchedUserEmail = result.match.email;
                matchedUserPhoneNumber = result.match.phone;
                loading = false;
                if (matchStatus === 'ACCEPTED') {
                    setTimeout(() => {
                        playMatchFoundAnimation();
                    }, 300);
                }
            } else if (result.status === 'no_match') {
                playSadAnimation();
                loading = false;
            } else if (result.status === 'not_registered') {
                playNotRegisteredAnimation();
                loading = false;
            }
        } catch (error) {
            console.error('Error checking Round 1 results:', error);
            loading = false;
        }
    });

    // Cleanup and animation load triggers using normal Svelte reactivity
    import { afterUpdate, onDestroy } from 'svelte';

    // Cleanup riveInstance and stop hearts on destroy
    onDestroy(() => {
      if (riveInstance) {
        riveInstance.cleanup();
      }
      stopHeartAnimation();
    });

    // Load animation when canvas and animation are set
    $: if (canvas && currentAnimation) {
      loadAnimation();
    }

    // Create floating hearts for PENDING and DECLINED status pages
    let pendingHeartInterval: any = null;
    $: {
      if (matchStatus === 'PENDING' || matchStatus === 'DECLINED') {
        if (!pendingHeartInterval) {
          pendingHeartInterval = setInterval(() => {
            createHeart();
          }, 1500);
        }
      } else {
        if (pendingHeartInterval) {
          clearInterval(pendingHeartInterval);
          pendingHeartInterval = null;
        }
      }
    }
</script>

{#if loading}
    <div class="bg-white flex items-center justify-center w-screen h-screen">
        <div class="text-center">
            <div class="w-16 h-16 border-4 border-t-transparent rounded-full animate-spin mx-auto mb-4" style="border-color: var(--primary-color); border-top-color: transparent;"></div>
            <p class="text-xl font-semibold" style="color: var(--primary-color); font-family: 'Nunito', sans-serif;">
                Checking your results...
            </p>
        </div>
    </div>
{:else if resultStatus === 'not_published'}
    <div class="bg-white flex items-center justify-center w-screen h-screen">
        <div class="text-center px-4">
            <div class="text-6xl mb-4">⏳</div>
            <p class="text-2xl font-bold mb-2" style="color: var(--primary-color); font-family: 'Nunito', sans-serif;">
                Results Not Yet Published
            </p>
            <p class="text-lg" style="color: var(--secondary-color); font-family: 'Nunito', sans-serif;">
                Round 1 results will be announced soon. Stay tuned!
            </p>
        </div>
    </div>
{:else if resultStatus === 'not_registered'}
    <div class="bg-white flex flex-col items-center justify-center gap-4 relative z-10">
      {#if currentAnimation}
        <canvas bind:this={canvas} class="w-[900px] h-[900px] max-w-[90vw] max-h-[75vh] object-contain shrink-0"></canvas>
      {:else}
        <p class="text-2xl font-semibold" style="color: var(--primary-color); font-family: 'Nunito', sans-serif;">
          You're not registered for Round 1
        </p>
      {/if}
      <div class="flex flex-col items-center gap-4 text-center px-4">
        <p class="text-2xl font-semibold" style="color: var(--primary-color); font-family: 'Nunito', sans-serif;">
          {currentText}
        </p>
        <p class="text-lg font-bold" style="color: var(--secondary-color); font-family: 'Nunito', sans-serif;">
          Stay tuned for Round 2! 💕
        </p>
        <p class="text-sm opacity-70 mt-2" style="color: var(--secondary-color); font-family: 'Nunito', sans-serif;">
          You'll have another chance to find your perfect match very soon
        </p>
      </div>
    </div>
{:else if resultStatus === 'no_match'}
    <div class="bg-white flex flex-col items-center justify-center gap-4 relative z-10">
      <canvas bind:this={canvas} class="w-[900px] h-[900px] max-w-[90vw] max-h-[75vh] object-contain shrink-0"></canvas>
      <div class="flex flex-col items-center gap-4 text-center px-4">
        <p class="text-2xl font-semibold" style="color: var(--primary-color); font-family: 'Nunito', sans-serif;">
          {currentText}
        </p>
        <p class="text-lg font-bold" style="color: var(--secondary-color); font-family: 'Nunito', sans-serif;">
          You will be automatically enrolled in Round 2!
        </p>
        <p class="text-sm opacity-70 mt-2" style="color: var(--secondary-color); font-family: 'Nunito', sans-serif;">
          We'll find you a perfect match in the next round ✨
        </p>
      </div>
    </div>
{:else if resultStatus === 'match_found'}
    {#if matchStatus === 'ACCEPTED'}
      <div class="bg-white flex justify-center items-center w-screen h-screen overflow-hidden relative">
        <div class="absolute top-4 right-4 z-50">
          <SignOutButton />
        </div>

        {#if !matchRevealed}
          <div class="flex flex-col items-center justify-center gap-4 relative z-10">
            <canvas bind:this={canvas} class="w-[900px] h-[900px] max-w-[90vw] max-h-[75vh] object-contain shrink-0"></canvas>
            <div class="flex flex-col items-center gap-4 text-center px-4">
              <p class="text-2xl font-semibold" style="color: var(--primary-color); font-family: 'Nunito', sans-serif;">
                {currentText}
              </p>
              <button 
                on:click={handleRevealMatch}
                class="reveal-button px-8 py-4 rounded-full text-white text-xl font-bold cursor-pointer"
                style="font-family: 'Nunito', sans-serif; background-color: var(--primary-color);"
              >
                Reveal Match
              </button>
            </div>
          </div>
        {:else}
          <div class="flex flex-col items-center justify-center gap-4 text-center px-4 relative z-10">
            <p class="text-3xl font-semibold" style="color: var(--secondary-color); font-family: 'Nunito', sans-serif;">
              You've been matched with
            </p>
            <p class="text-7xl font-bold typewriter" style="color: var(--primary-color); font-family: 'Nunito', sans-serif;">
              {displayedName}<span class="cursor">|</span>
            </p>
            {#if showPhoneNumber}
              <div class="phone-container fade-in" style="background-color: var(--primary-color);">
                <img src="/icons/phone-icon.png" alt="phone" class="phone-icon" />
                <span class="phone-number"><a class="no-decor" href="https://wa.me/+91{matchedUserPhoneNumber}">{matchedUserPhoneNumber}</a></span>
              </div>
              <p class="text-sm opacity-70 mt-2 fade-in" style="color: var(--secondary-color); font-family: 'Nunito', sans-serif;">
                Email: {matchedUserEmail}
              </p>
            {/if}
          </div>
        {/if}
      </div>
    {:else if matchStatus === 'PENDING'}
      <!-- PENDING Status Page - Round 2 Application -->
      <div class="flex items-center justify-center min-h-screen px-4">
          <!-- Floating Hearts Background -->
          <div class="floating-hearts-container">
              {#each hearts as heart (heart.id)}
                  <img 
                      src="/images/heart.png"
                      alt="heart"
                      class="floating-heart-pending"
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
          
          <div class="flex flex-col items-center justify-center gap-8 max-w-3xl w-full relative z-10 text-center">
              <div class="flex flex-col items-center gap-6 px-6 py-8 rounded-2xl" style="background-color: rgba(255, 255, 255, 0.9);">
                  <div class="flex flex-col items-center gap-4">
                      <div class="text-6xl">💕</div>
                      <h1 class="text-3xl md:text-4xl font-bold" style="color: var(--secondary-color); font-family: 'Nunito', sans-serif;">
                          Thank You for Applying!
                      </h1>
                      <p class="text-lg md:text-xl font-semibold max-w-xl" style="color: var(--primary-color); font-family: 'Nunito', sans-serif;">
                          Round 2 will start very soon
                      </p>
                      <p class="text-base md:text-lg max-w-xl" style="color: var(--secondary-color); font-family: 'Nunito', sans-serif;">
                          We're preparing the next round of matches. You'll be notified when Round 2 begins!
                      </p>
                  </div>
                  <div class="flex items-center gap-3 mt-4">
                      <div class="animate-pulse">
                          <img src="/images/heart.png" alt="heart" class="w-8 h-8" />
                      </div>
                      <p class="text-sm font-semibold italic" style="color: var(--secondary-color); font-family: 'Nunito', sans-serif;">
                          Stay tuned for updates!
                      </p>
                      <div class="animate-pulse">
                          <img src="/images/heart.png" alt="heart" class="w-8 h-8" />
                      </div>
                  </div>
              </div>
          </div>
      </div>
    {:else if matchStatus === 'DECLINED'}
      <!-- DECLINED Status Page -->
      <div class="flex items-center justify-center min-h-screen px-4">
          <!-- Floating Hearts Background -->
          <div class="floating-hearts-container">
              {#each hearts as heart (heart.id)}
                  <img 
                      src="/images/heart.png"
                      alt="heart"
                      class="floating-heart-pending"
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
          
          <div class="flex flex-col items-center justify-center gap-8 max-w-3xl w-full relative z-10 text-center">
              <div class="flex flex-col items-center gap-6 px-6 py-8 rounded-2xl" style="background-color: rgba(255, 255, 255, 0.9);">
                  <div class="flex flex-col items-center gap-4">
                      <div class="text-6xl">💝</div>
                      <h1 class="text-3xl md:text-4xl font-bold" style="color: var(--secondary-color); font-family: 'Nunito', sans-serif;">
                          Thank You for Registering With Us!
                      </h1>
                      <p class="text-lg md:text-xl font-semibold max-w-xl" style="color: var(--primary-color); font-family: 'Nunito', sans-serif;">
                          We appreciate your participation
                      </p>
                      <p class="text-base md:text-lg max-w-xl" style="color: var(--secondary-color); font-family: 'Nunito', sans-serif;">
                          We hope you had a wonderful experience with Find Your Date. We wish you all the best!
                      </p>
                  </div>
                  <div class="flex items-center gap-3 mt-4">
                      <div class="animate-pulse">
                          <img src="/images/heart.png" alt="heart" class="w-8 h-8" />
                      </div>
                      <p class="text-sm font-semibold italic" style="color: var(--secondary-color); font-family: 'Nunito', sans-serif;">
                          Thank you for being part of our journey!
                      </p>
                      <div class="animate-pulse">
                          <img src="/images/heart.png" alt="heart" class="w-8 h-8" />
                      </div>
                  </div>
              </div>
          </div>
      </div>
    {:else}
      <!-- Default match_found UI (Reveal Match etc) -->
      <div class="bg-white flex flex-col items-center justify-center gap-4 relative z-10">
        <canvas bind:this={canvas} class="w-[900px] h-[900px] max-w-[90vw] max-h-[75vh] object-contain shrink-0"></canvas>
        <div class="flex flex-col items-center gap-4 text-center px-4">
          {#if currentText}
            <p class="text-2xl font-semibold" style="color: var(--primary-color); font-family: 'Nunito', sans-serif;">
              {currentText}{#if showDots}<span class="dots"></span>{/if}
            </p>
          {/if}
          {#if showButton}
            <button 
              on:click={handleRevealMatch}
              class="reveal-button px-8 py-4 rounded-full text-white text-xl font-bold cursor-pointer"
              style="font-family: 'Nunito', sans-serif; background-color: var(--primary-color);"
            >
              Reveal Match
            </button>
          {/if}
        </div>
      </div>
    {/if}
{:else}
    <div class="flex flex-col items-center justify-center gap-4 relative z-10">
      <p class="text-2xl font-semibold" style="color: var(--primary-color); font-family: 'Nunito', sans-serif;">
        Something went wrong loading your result.
      </p>
      <p class="text-lg font-bold" style="color: var(--secondary-color); font-family: 'Nunito', sans-serif;">
        Please refresh or try again later.
      </p>
    </div>
{/if}

<!-- Round 2 Choice Modal -->
{#if showModal}
  <div class="modal-overlay" on:click={() => showModal = false}>
    <div class="modal-content" on:click={(e) => e.stopPropagation()}>
      <h2 class="text-2xl font-bold mb-4" style="color: var(--secondary-color); font-family: 'Nunito', sans-serif;">
        Would you like to be considered for Round 2?
      </h2>
      <p class="text-base mb-6" style="color: var(--secondary-color); font-family: 'Nunito', sans-serif;">
        You can choose to be matched with someone new in Round 2, or opt out completely.
      </p>
      <div class="flex gap-4 justify-center">
        <button 
          on:click={() => handleRound2Choice(false)}
          class="modal-button px-6 py-3 rounded-full text-white font-bold"
          style="font-family: 'Nunito', sans-serif; background-color: #999;"
        >
          No Round 2
        </button>
        <button 
          on:click={() => handleRound2Choice(true)}
          class="modal-button px-6 py-3 rounded-full text-white font-bold"
          style="font-family: 'Nunito', sans-serif; background-color: var(--primary-color);"
        >
          Apply Round 2
        </button>
      </div>
    </div>
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

  .phone-container {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 16px 32px;
    border-radius: 50px;
  }

  .phone-icon {
    width: 24px;
    height: 24px;
    filter: brightness(0) invert(1);
  }

  .phone-number {
    color: white;
    font-family: 'Nunito', sans-serif;
    font-size: 1.5rem;
    font-weight: 600;
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

  .rematch-button {
    transition: all 0.3s ease;
  }

  .rematch-button:hover {
    filter: brightness(1.1);
    transform: scale(1.05);
  }
  
  .decline-button {
    transition: all 0.3s ease;
  }

  .decline-button:hover {
    filter: brightness(1.1);
    transform: scale(1.05);
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
  }
  
  .modal-button {
    transition: all 0.3s ease;
    cursor: pointer;
  }
  
  .modal-button:hover {
    filter: brightness(1.1);
    transform: scale(1.05);
  }
  
  .no-decor {
    text-decoration: none;
    color: inherit;
  }
  
  .floating-hearts-container {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    overflow: hidden;
    z-index: 0;
  }

  .floating-heart-pending {
    position: absolute;
    bottom: -60px;
    opacity: 0;
    animation: floatUpPending linear forwards;
    pointer-events: none;
  }

  @keyframes floatUpPending {
    0% {
      bottom: -60px;
      opacity: 0;
    }
    10% {
      opacity: 0.8;
    }
    90% {
      opacity: 0.8;
    }
    100% {
      bottom: 110vh;
      opacity: 0;
    }
  }

  @media (max-width: 550px) {
    canvas {
      height: 300px !important;
    }
  }
</style>