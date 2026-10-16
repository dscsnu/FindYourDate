<script lang="ts">
	import favicon from '$lib/assets/favicon.svg';
	import "../app.css";
	import { fade } from 'svelte/transition';
	import { page } from '$app/state';
	import { configStore } from '$lib/stores/config';
	import FormsClosedPage from '$lib/components/FormsClosedPage.svelte';

	let { children } = $props();
	
	let formsClosed = $state(false);
	
	configStore.subscribe(config => {
		formsClosed = config.formsClosed;
	});
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

<div class="min-h-screen" style="background-color: var(--background-color);">
	{#if formsClosed}
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
