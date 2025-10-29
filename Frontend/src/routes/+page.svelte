<script>
  import { goto } from "$app/navigation";
	import { onMount } from 'svelte';
	import { authStore } from '$lib/stores/auth';
	import { api, API_BASE_URL } from '$lib/api';
    import { configStore } from '$lib/stores/config';

	let hearts = $state([]);
	let heartIdCounter = 0;
	const MAX_HEARTS = 4;
	let loading = $state(false);
	let checkingStatus = $state(true);
  let round1ResultPublished = $state(false);
	if(round1ResultPublished){
		goto('/endScreen');
	}
	async function checkUserStatus(session) {
		try {
			// Check user status in backend using cookie authentication
			const response = await fetch(`${API_BASE_URL}/status/user-status?email=${encodeURIComponent(session.user.email)}`, {
				credentials: 'include'
			});

			if (!response.ok) {
				throw new Error('Failed to check user status');
			}

			const data = await response.json();
			
			// Redirect based on status
			if (data.redirect_to === 'form') {
				// User needs to fill form
				goto('/userForm');
			} else if (data.redirect_to === 'chat') {
				// User needs to complete chat
				sessionStorage.setItem('user_id', data.user_id);
				goto('/aiChatRoom');
			} else if (data.redirect_to === 'complete') {
				// User has completed everything - show end screen or matches
				sessionStorage.setItem('user_id', data.user_id);
				goto('/endScreen');
			}
		} catch (error) {
			console.error('Error checking user status:', error);
			// If check fails, let them stay on landing page
		} finally {
			checkingStatus = false;
		}
	}

	async function signInWithGoogle() {
		loading = true;
		try {
			// Call backend to get Google OAuth URL
			const data = await api.auth.googleLogin();
			
			// Redirect to Google OAuth
			window.location.href = data.url;
		} catch (error) {
			console.error('Sign in error:', error);
			alert('Failed to sign in. Please try again.');
			loading = false;
		}
	}

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

	onMount(async () => {
		// Load existing session if available
		await authStore.loadSession();
		
		// Check if user is already authenticated
		const currentSession = await new Promise(resolve => {
			const unsubscribe = authStore.subscribe(value => {
				resolve(value);
				unsubscribe();
			});
		});
		
		if (currentSession?.authenticated) {
			// User is authenticated, check their status
			await checkUserStatus(currentSession);
		} else {
			// Not authenticated, stay on landing page
			checkingStatus = false;
		}

		// Create initial hearts
		const interval = setInterval(() => {
			createHeart();
		}, 1500); // Create a new heart every 1.5 seconds

		return () => clearInterval(interval);
	});
</script>

{#if checkingStatus}
	<div class="flex items-center justify-center min-h-screen" style="background-color: var(--primary-color);">
		<div class="text-center">
			<div class="w-16 h-16 border-4 border-white border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
			<p class="text-xl font-semibold text-white" style="font-family: 'Nunito', sans-serif;">
				Loading...
			</p>
		</div>
	</div>
{:else}
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

	<div class="flex flex-col lg:flex-row items-center justify-center gap-8 lg:gap-16 max-w-6xl w-full relative z-10">
		<!-- Image Section -->
		<div class="shrink-0">
			<img 
				src="/images/logo.png" 
				alt="Find Your Date placeholder" 
				class="max-w-md w-full h-auto rounded-lg"
			/>
		</div>
		
		<!-- Text and Button Section -->
		<div class="text-center lg:text-left flex flex-col items-center lg:items-start">
			<p class="text-lg md:text-xl font-bold mb-6 max-w-md" style="color: var(--secondary-color); font-family: 'Nunito', sans-serif;">
				Find your ideal prom date! 
				Tell us who you are, 
				and let our AI match you with your perfect vibe.
			</p>
			<button onclick={signInWithGoogle} 
				class="flex items-center justify-center gap-3 px-6 py-3 bg-white border border-gray-300 rounded-full text-gray-700 font-medium text-base hover:bg-gray-50 hover:border-gray-400 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
				style="font-family: 'Montserrat', sans-serif;"
				disabled={loading}
			>
				{#if loading}
					<div class="w-5 h-5 border-2 border-gray-700 border-t-transparent rounded-full animate-spin"></div>
					<span>Signing in...</span>
				{:else}
					<svg width="20" height="20" viewBox="0 0 24 24">
						<path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
						<path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
						<path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
						<path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
					</svg>
					<span>Sign in with Google</span>
				{/if}
			</button>
			<div class="ml-2 mt-3 flex items-center gap-2">
				<img src="/icons/information-icon.png" alt="Info" class="w-4 h-4" />
				<p class="text-sm font-semibold" style="color: white; font-family: 'Nunito', sans-serif;">
					Sign in with your SNU mail ID
				</p>
			</div>
		</div>
	</div>
</div>
{/if}

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