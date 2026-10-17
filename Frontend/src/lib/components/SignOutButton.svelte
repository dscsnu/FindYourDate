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
	class="sign-out-btn px-3 sm:px-4 py-1.5 sm:py-2 rounded-full font-semibold text-xs sm:text-sm whitespace-nowrap transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
>
	{#if isLoggingOut}
		<span class="flex items-center gap-2">
			<div class="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"></div>
			Signing out...
		</span>
	{:else}
		Sign Out
	{/if}
</button>

<style>
	.sign-out-btn {
		/* White pill with dark text stays readable on every pink background */
		background-color: white;
		color: var(--secondary-color);
		box-shadow: 0 2px 8px rgba(49, 48, 53, 0.12);
	}

	.sign-out-btn:hover:not(:disabled) {
		background-color: #fdf0f4;
		transform: scale(1.02);
	}

	.sign-out-btn:active:not(:disabled) {
		transform: scale(0.98);
	}
</style>
