<script lang="ts">
	import { onMount } from 'svelte';

	interface Heart {
		id: number;
		left: number;
		duration: number;
		delay: number;
		size: number;
		rotation: number;
	}

	let hearts = $state<Heart[]>([]);
	let heartIdCounter = 0;
	const MAX_HEARTS = 4;

	function createHeart() {
		if (hearts.length >= MAX_HEARTS) return;

		const heart = {
			id: heartIdCounter++,
			left: Math.random() * 100, // Random horizontal position (0-100%)
			duration: 3 + Math.random() * 2, // Random duration between 3-5 seconds
			delay: Math.random() * 1, // Random delay 0-1 second
			size: 100 + Math.random() * 50, // Random size between 100-150px
			rotation: (Math.random() * 90) - 45 // Random rotation between -45 to 45 degrees
		};

		hearts = [...hearts, heart];

		// Remove heart after animation completes
		setTimeout(() => {
			hearts = hearts.filter(h => h.id !== heart.id);
		}, (heart.duration + heart.delay) * 1000);
	}

	onMount(() => {
		// Create initial hearts
		const interval = setInterval(() => {
			createHeart();
		}, 1500); // Create a new heart every 1.5 seconds

		return () => clearInterval(interval);
	});
</script>

<div class="flex items-center justify-center min-h-screen px-4">
	<!-- Floating Hearts Background -->
	<div class="floating-hearts-container">
		{#each hearts as heart (heart.id)}
			<img 
				src="/images/heart.png"
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

	<div class="flex flex-col items-center justify-center gap-8 max-w-3xl w-full relative z-10 text-center">
		<!-- Logo/Image -->
		<div class="shrink-0">
			<img 
				src="/images/logo.png" 
				alt="Find Your Date" 
				class="max-w-sm w-full h-auto rounded-lg mx-auto"
			/>
		</div>
		
		<!-- Announcement Section -->
		<div class="flex flex-col items-center gap-6 px-6 py-8 rounded-2xl" style="background-color: rgba(255, 255, 255, 0.9);">
			<div class="flex flex-col items-center gap-4">
				<!-- Icon or emoji -->
				<div class="text-6xl">
					💕
				</div>
				
				<!-- Main heading -->
				<h1 class="text-3xl md:text-4xl font-bold" style="color: var(--secondary-color); font-family: 'Nunito', sans-serif;">
					Forms Are Now Closed!
				</h1>
				
				<!-- Message -->
				<p class="text-lg md:text-xl font-semibold max-w-xl" style="color: var(--primary-color); font-family: 'Nunito', sans-serif;">
					Registration has ended.
				</p>
				
				<p class="text-base md:text-lg max-w-xl" style="color: var(--secondary-color); font-family: 'Nunito', sans-serif;">
					We're matching everyone who registered with their perfect prom date. 
					Results will be announced very soon!
				</p>
			</div>
			
			<!-- Additional decorative element -->
			<div class="flex items-center gap-3 mt-4">
				<div class="animate-pulse">
					<img src="/images/heart.png" alt="heart" class="w-8 h-8" />
				</div>
				<p class="text-sm font-semibold italic" style="color: var(--secondary-color); font-family: 'Nunito', sans-serif;">
					Stay tuned for the big reveal!
				</p>
				<div class="animate-pulse">
					<img src="/images/heart.png" alt="heart" class="w-8 h-8" />
				</div>
			</div>
		</div>
	</div>
</div>

<style>
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

	.floating-heart {
		position: absolute;
		bottom: -60px;
		opacity: 0;
		animation: floatUp linear forwards;
		pointer-events: none;
	}

	@keyframes floatUp {
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
</style>
