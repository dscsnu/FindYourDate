<script>
    import * as rive from "@rive-app/canvas";

    let canvas;
    let currentAnimation = '';
    let currentText = $state('');
    let showDots = $state(false);
    let showButton = $state(false);
    let riveInstance = null;

    function playAnalyzingAnimation() {
      currentAnimation = '/animations/heart-hi.riv';
      currentText = 'Analyzing your vibe';
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
      // Handle reveal match logic here
      console.log('Revealing match...');
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

    $effect(() => {
      if (!canvas) return;

      // Initialize with analyzing animation by default
      setTimeout(() => {
        playMatchFoundAnimation();
      }, 0);

      return () => {
        if (riveInstance) {
          riveInstance.cleanup();
        }
      }
    });
</script>

<div class="bg-white flex justify-center items-center w-screen h-screen overflow-hidden">
  <div class="flex flex-col items-center justify-center gap-4">
    <canvas bind:this={canvas} class="w-[900px] h-[900px] max-w-[90vw] max-h-[75vh] object-contain shrink-0"></canvas>
    <div class="flex flex-col items-center gap-4 text-center px-4">
      {#if currentText}
        <p class="text-2xl font-semibold" style="color: var(--primary-color); font-family: 'Nunito', sans-serif;">
          {currentText}{#if showDots}<span class="dots"></span>{/if}
        </p>
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
</div>

<style>
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
</style>