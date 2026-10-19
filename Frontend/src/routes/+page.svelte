<script>
  import { goto, preloadCode } from "$app/navigation";
	import { onMount } from 'svelte';
	import { get } from 'svelte/store';
	import { authStore } from '$lib/stores/auth';
	import { api } from '$lib/api';
	import { configStore } from '$lib/stores/config';
	import { fadeIn } from '$lib/actions/fadeIn';
	import FloatingHearts from '$lib/components/FloatingHearts.svelte';
	import LoadingScreen from '$lib/components/LoadingScreen.svelte';

	let loading = $state(false);
	let checkingStatus = $state(true);
  let round1ResultPublished = $state(false);

	async function checkUserStatus() {
		try {
			// Identity comes from the session cookie, not a query param.
			const data = await api.status.userStatus();

			// If Round 1 results are published, always take to endScreen
			if(round1ResultPublished){
				if (data.user_id) {
					sessionStorage.setItem('user_id', data.user_id);
				}
				goto('/endScreen');
				return;
			}
			
			// Redirect based on status (only if results not published)
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
		// Drop anything left over from a previous user on this device.
		try {
			localStorage.clear();
			sessionStorage.clear();
		} catch {
			// Storage can be blocked (private mode); nothing to clear then.
		}
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

	onMount(async () => {
		// Most visitors go straight to the form next; fetch its code while they read.
		preloadCode('/userForm');

		round1ResultPublished = get(configStore).round1ResultPublished;

		await authStore.loadSession();
		const currentSession = get(authStore);

		if (currentSession?.authenticated) {
			await checkUserStatus();
		} else {
			checkingStatus = false;
		}
	});
</script>

{#if checkingStatus}
	<LoadingScreen />
{:else}
<main class="flex items-center justify-center min-h-screen px-6 py-12 lg:px-12">
	<FloatingHearts />

	<div class="flex flex-col lg:flex-row items-center justify-center gap-8 lg:gap-20 max-w-5xl w-full relative z-10">
		<!-- Image Section -->
		<div class="shrink-0 w-full max-w-[18rem] sm:max-w-sm lg:max-w-md lg:flex-1 landing-rise">
			<img 
				src="/images/logo.webp" 
				alt="Find Your Date" 
				width="900"
				height="900"
				fetchpriority="high"
				use:fadeIn
				class="w-full h-auto rounded-lg drop-shadow-xl"
			/>
		</div>
		
		<!-- Text and Button Section -->
		<div class="text-center lg:text-left flex flex-col items-center lg:items-start lg:flex-1 landing-rise" style="animation-delay: 120ms;">
			<p class="text-lg md:text-xl lg:text-2xl font-bold lg:font-extrabold mb-6 max-w-md lg:leading-snug text-balance" style="color: var(--secondary-color);">
				Find your ideal prom date! 
				Tell us who you are, 
				and let our AI match you with your perfect vibe.
			</p>
			<button onclick={signInWithGoogle} 
				class="flex items-center justify-center gap-3 px-6 py-3 bg-white border border-gray-300 rounded-full text-gray-700 font-semibold text-base shadow-sm hover:shadow-md hover:-translate-y-0.5 hover:border-gray-400 active:translate-y-0 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:translate-y-0"
				disabled={loading}
			>
				{#if loading}
					<div class="w-5 h-5 border-2 border-gray-700 border-t-transparent rounded-full animate-spin"></div>
					<span>Signing in...</span>
				{:else}
					<svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true">
						<path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
						<path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
						<path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
						<path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
					</svg>
					<span>Sign in with Google</span>
				{/if}
			</button>
			<div class="ml-2 mt-3 flex items-center gap-2">
				<img src="/icons/information-icon.png" alt="" width="64" height="64" class="w-4 h-4" />
				<p class="text-sm font-semibold" style="color: white;">
					Sign in with your SNU mail ID
				</p>
			</div>
		</div>
	</div>
</main>
{/if}

<style>
	.landing-rise {
		animation: rise 0.7s var(--ease-out) both;
	}

	@keyframes rise {
		from {
			opacity: 0;
			transform: translate3d(0, 16px, 0);
		}
		to {
			opacity: 1;
			transform: none;
		}
	}
</style>
