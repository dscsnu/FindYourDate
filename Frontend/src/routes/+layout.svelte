<script lang="ts">
	import favicon from '$lib/assets/favicon.svg';
	import "../app.css";
	import { fade } from 'svelte/transition';
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import { configStore } from '$lib/stores/config';
	import FormsClosedPage from '$lib/components/FormsClosedPage.svelte';

	let { children } = $props();
	
	let formsClosed = $state(false);
	let registrationsClosed = $state(false);

	configStore.subscribe(config => {
		formsClosed = config.formsClosed;
		registrationsClosed = config.registrationsClosed;
	});

	// Landing page sends anyone who hasn't finished signing up to one of these.
	let onSignupPage = $derived(['/userForm', '/aiChatRoom'].includes(page.url.pathname));

	$effect(() => {
		if (registrationsClosed && onSignupPage) goto('/endScreen', { replaceState: true });
	});
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

<div class="min-h-screen" style="background-color: var(--background-color);">
	{#if registrationsClosed && onSignupPage}
		<!-- redirecting to /endScreen -->
	{:else if formsClosed}
		<FormsClosedPage />
	{:else}
		<!-- Fade each route in; no outro, so pages never overlap mid-navigation -->
		{#key page.url.pathname}
			<div class="min-h-screen" in:fade={{ duration: 250 }}>
				{@render children?.()}
			</div>
		{/key}
	{/if}
</div>
