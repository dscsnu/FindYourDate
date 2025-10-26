<script>
	import { goto } from '$app/navigation';
	import { authStore } from '$lib/stores/auth';

	let isLoggingOut = $state(false);

	async function handleSignOut() {
		if (isLoggingOut) return;
		
		isLoggingOut = true;
		try {
			await authStore.logout();
			goto('/');
		} catch (error) {
			console.error('Sign out error:', error);
			alert('Failed to sign out. Please try again.');
		} finally {
			isLoggingOut = false;
		}
	}
</script>

<button
	onclick={handleSignOut}
	disabled={isLoggingOut}
	class="sign-out-btn px-4 py-2 rounded-full font-semibold text-sm transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
	style="font-family: 'Nunito', sans-serif;"
>
	{#if isLoggingOut}
		<span class="flex items-center gap-2">
			<div class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
			Signing out...
		</span>
	{:else}
		Sign Out
	{/if}
</button>

<style>
	.sign-out-btn {
		background-color: var(--primary-color);
		color: white;
		border: none;
	}

	.sign-out-btn:hover:not(:disabled) {
		opacity: 0.9;
		transform: scale(1.02);
	}

	.sign-out-btn:active:not(:disabled) {
		transform: scale(0.98);
	}
</style>
