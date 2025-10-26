<!-- Example: Protected Route with Auth Check -->
<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { authStore } from '$lib/stores/auth';
	
	let session = $state(null);
	let loading = $state(true);
	
	// Subscribe to auth store
	authStore.subscribe(value => {
		session = value;
	});
	
	onMount(async () => {
		// Load session if exists
		await authStore.loadSession();
		
		// Check if user is authenticated
		const currentSession = await new Promise(resolve => {
			const unsubscribe = authStore.subscribe(value => {
				resolve(value);
				unsubscribe();
			});
		});
		
		if (!currentSession) {
			// Redirect to home if not authenticated
			goto('/');
			return;
		}
		
		loading = false;
	});
	
	async function handleLogout() {
		await authStore.logout();
		goto('/');
	}
</script>

{#if loading}
	<div class="flex items-center justify-center min-h-screen">
		<div class="text-center">
			<div class="w-16 h-16 border-4 border-pink-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
			<p class="text-xl">Loading...</p>
		</div>
	</div>
{:else if session?.user}
	<div class="p-8">
		<div class="max-w-4xl mx-auto">
			<!-- User Info Card -->
			<div class="bg-white rounded-lg shadow-lg p-6 mb-6">
				<div class="flex items-center justify-between mb-4">
					<h1 class="text-2xl font-bold">Welcome!</h1>
					<button
						onclick={handleLogout}
						class="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
					>
						Logout
					</button>
				</div>
				
				<div class="space-y-2">
					<p><strong>Email:</strong> {session.user.email}</p>
					<p><strong>User ID:</strong> {session.user.id}</p>
					{#if session.user.user_metadata?.full_name}
						<p><strong>Name:</strong> {session.user.user_metadata.full_name}</p>
					{/if}
					{#if session.user.user_metadata?.avatar_url}
						<img 
							src={session.user.user_metadata.avatar_url} 
							alt="Profile" 
							class="w-16 h-16 rounded-full mt-4"
						/>
					{/if}
				</div>
			</div>
			
			<!-- Token Info (for debugging, remove in production) -->
			<div class="bg-gray-100 rounded-lg p-6">
				<h2 class="text-lg font-semibold mb-2">Session Info (Debug)</h2>
				<div class="space-y-1 text-sm">
					<p><strong>Token Type:</strong> Bearer</p>
					<p><strong>Expires At:</strong> {new Date(session.expires_at * 1000).toLocaleString()}</p>
					<p><strong>Access Token:</strong> {session.access_token.substring(0, 20)}...</p>
				</div>
			</div>
		</div>
	</div>
{:else}
	<div class="flex items-center justify-center min-h-screen">
		<div class="text-center">
			<p class="text-xl mb-4">Not authenticated</p>
			<button
				onclick={() => goto('/')}
				class="px-6 py-3 bg-pink-500 text-white rounded-lg hover:bg-pink-600 transition-colors"
			>
				Go to Home
			</button>
		</div>
	</div>
{/if}
