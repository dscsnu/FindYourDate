<script lang="ts">
	import { fade } from 'svelte/transition';

	let { message = 'Loading...' }: { message?: string } = $props();
</script>

<div
	class="flex-1 min-h-screen w-full flex items-center justify-center px-4"
	style="background-color: var(--primary-color);"
	role="status"
	aria-live="polite"
	in:fade={{ duration: 200, delay: 150 }}
>
	<div class="text-center">
		<div class="w-16 h-16 border-4 border-white border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
		<p class="text-xl font-semibold text-white">
			{message}
		</p>
	</div>
</div>
