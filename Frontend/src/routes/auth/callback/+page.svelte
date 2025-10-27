<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { authStore } from '$lib/stores/auth';
	import { browser } from '$app/environment';

	let error = $state<string | null>(null);
	let loading = $state(true);

	onMount(async () => {
		if (!browser) return;

		try {
			// Get the full URL hash and search params
			const hashParams = new URLSearchParams(window.location.hash.substring(1));
			const searchParams = new URLSearchParams(window.location.search);
			
			// Check for error in either hash or search params
			const errorParam = hashParams.get('error') || searchParams.get('error');
			const errorDescription = hashParams.get('error_description') || searchParams.get('error_description');
			
			if (errorParam) {
				console.error('OAuth error:', errorParam, errorDescription);
				error = errorDescription || errorParam;
				loading = false;
				return;
			}

			// Get access_token from hash (Supabase implicit flow)
			const accessToken = hashParams.get('access_token');
			const refreshToken = hashParams.get('refresh_token');
			
			if (accessToken) {
				// Store tokens in backend as httpOnly cookies
				const API_BASE_URL = import.meta.env.PUBLIC_API_URL || 'http://localhost:8000';
				const response = await fetch(`${API_BASE_URL}/auth/store-session`, {
					method: 'POST',
					headers: {
						'Content-Type': 'application/json',
					},
					credentials: 'include',
					body: JSON.stringify({
						access_token: accessToken,
						refresh_token: refreshToken
					})
				});

				if (!response.ok) {
					throw new Error('Failed to store session');
				}

				// Load session into store
				await authStore.loadSession();

				// Clear URL
				window.history.replaceState({}, '', '/auth/callback');

				// Redirect to user form
				await goto('/userForm');
			} else {
				error = 'No access token received';
				loading = false;
			}
		} catch (err) {
			console.error('Auth error:', err);
			error = err instanceof Error ? err.message : 'Authentication failed';
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
