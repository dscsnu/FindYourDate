<script lang="ts">
	import favicon from '$lib/assets/favicon.svg';
	import "../app.css";
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
		{@render children?.()}
	{/if}
</div>
