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

	const MAX_HEARTS = 4;

	let hearts = $state<Heart[]>([]);
	let heartIdCounter = 0;

	function createHeart() {
		if (hearts.length >= MAX_HEARTS || document.hidden) return;

		const heart: Heart = {
			id: heartIdCounter++,
			left: Math.random() * 100, // Random horizontal position (0-100%)
			duration: 3 + Math.random() * 2, // Random duration between 3-5 seconds
			delay: Math.random() * 1, // Random delay 0-1 second
			size: 100 + Math.random() * 50, // Random size between 100-150px
			rotation: Math.random() * 90 - 45 // Random rotation between -45 to 45 degrees
		};

		hearts = [...hearts, heart];
	}

	function removeHeart(id: number) {
		hearts = hearts.filter((h) => h.id !== id);
	}

	onMount(() => {
		// Decorative only: skip entirely for people who asked for less motion.
		if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

		const interval = setInterval(createHeart, 1500);
		return () => clearInterval(interval);
	});
</script>

<div class="floating-hearts-container" aria-hidden="true">
	{#each hearts as heart (heart.id)}
		<img
			src="/images/heart.webp"
			alt=""
			width="300"
			height="294"
			decoding="async"
			class="floating-heart"
			onanimationend={() => removeHeart(heart.id)}
			style="
				left: {heart.left}%;
				animation-duration: {heart.duration}s;
				animation-delay: {heart.delay}s;
				width: {heart.size}px;
				height: auto;
				--rotation: {heart.rotation}deg;
			"
		/>
	{/each}
</div>

<style>
	.floating-hearts-container {
		position: fixed;
		inset: 0;
		pointer-events: none;
		overflow: hidden;
		z-index: 0;
	}

	.floating-heart {
		position: absolute;
		top: 100%;
		margin-left: -75px;
		opacity: 0;
		/* Animate transform/opacity only so this stays on the compositor */
		will-change: transform, opacity;
		animation-name: floatUp;
		animation-timing-function: linear;
		animation-fill-mode: both;
		pointer-events: none;
	}

	@keyframes floatUp {
		0% {
			transform: translate3d(0, 0, 0) rotate(var(--rotation));
			opacity: 0;
		}
		10% {
			opacity: 0.8;
		}
		90% {
			opacity: 0.8;
		}
		100% {
			transform: translate3d(0, calc(-110vh - 150px), 0) rotate(var(--rotation));
			opacity: 0;
		}
	}
</style>
