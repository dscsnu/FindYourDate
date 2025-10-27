<script lang="ts"></script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { authStore } from '$lib/stores/auth';
	import { api } from '$lib/api';

	let error = $state<string | null>(null);
	let loading = $state(true);

	onMount(async () => {
		const urlParams = new URLSearchParams(window.location.search);
		const code = urlParams.get('code');
		const errorParam = urlParams.get('error');
		const errorDescription = urlParams.get('error_description');

		// Check for OAuth errors
		if (errorParam) {
			console.error('OAuth error:', errorParam, errorDescription);
			error = errorDescription || errorParam;
			loading = false;
			return;
		}

		// If we have an OAuth code, exchange it for a session
		if (code) {
			try {
				console.log('Exchanging OAuth code for session...');
				
				// Exchange code for session tokens via backend
				const response = await fetch(`${api.auth.getBaseUrl()}/auth/session/exchange`, {
					method: 'POST',
					headers: {
						'Content-Type': 'application/json',
					},
					credentials: 'include', // Important: send/receive cookies
					body: JSON.stringify({ code })
				});

				if (!response.ok) {
					const errorData = await response.json();
					throw new Error(errorData.detail || 'Failed to exchange code for session');
				}

				const sessionData = await response.json();
				console.log('Session exchange successful');

				// Load the session into the store
				authStore.setSession(sessionData.user);

				// Clear URL parameters
				window.history.replaceState({}, '', '/auth/callback');

				// Small delay to ensure everything is set
				await new Promise(resolve => setTimeout(resolve, 100));

				// Redirect to user form
				await goto('/userForm');
			} catch (err) {
				console.error('Session exchange error:', err);
				error = err instanceof Error ? err.message : 'Authentication failed';
				loading = false;
			}
			return;
		}

		// Fallback: check for success parameter (old flow)
		const success = urlParams.get('success');
		if (success === 'true') {
			try {
				// Small delay to ensure cookies are properly set
				await new Promise(resolve => setTimeout(resolve, 200));
				
				// Load session from cookies
				await authStore.loadSession();

				// Clear URL parameters
				window.history.replaceState({}, '', '/auth/callback');

				// Redirect to user form
				await goto('/userForm');
			} catch (err) {
				console.error('Auth error:', err);
				error = err instanceof Error ? err.message : 'Authentication failed';
				loading = false;
			}
		} else {
			error = 'No authentication code received';
			loading = false;
		}
	});
</script>

<div class="flex items-center justify-center min-h-screen px-4">
	<div class="text-center">
		{#if loading}
			<div class="flex flex-col items-center gap-4">
				<div class="w-16 h-16 border-4 border-pink-500 border-t-transparent rounded-full animate-spin"></div>
				<p class="text-xl font-semibold" style="color: var(--secondary-color); font-family: 'Nunito', sans-serif;">
					Completing sign in...
				</p>
			</div>
		{:else if error}
			<div class="flex flex-col items-center gap-4">
				<svg class="w-16 h-16 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
				</svg>
				<p class="text-xl font-semibold text-red-500" style="font-family: 'Nunito', sans-serif;">
					Authentication Failed
				</p>
				<p class="text-gray-600" style="font-family: 'Nunito', sans-serif;">
					{error}
				</p>
				<button
					onclick={() => goto('/')}
					class="mt-4 px-6 py-3 bg-pink-500 text-white rounded-full font-medium hover:bg-pink-600 transition-all duration-200"
					style="font-family: 'Montserrat', sans-serif;"
				>
					Back to Home
				</button>
			</div>
		{/if}
	</div>
</div>
