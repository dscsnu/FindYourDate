<script lang="ts">
	import FloatingHearts from './FloatingHearts.svelte';
	import { fadeIn } from '$lib/actions/fadeIn';
	import SignOutButton from './SignOutButton.svelte';
</script>

<div class="absolute top-4 right-4 z-50"><SignOutButton /></div>

<div class="flex items-center justify-center min-h-screen px-4 py-10">
	<FloatingHearts />

	<div class="flex flex-col items-center justify-center gap-8 max-w-3xl w-full relative z-10 text-center">
		<!-- Logo/Image -->
		<div class="shrink-0 w-full max-w-[16rem] sm:max-w-sm">
			<img 
				src="/images/logo.webp" 
				alt="Find Your Date" 
				width="900"
				height="900"
				fetchpriority="high"
				use:fadeIn
				class="w-full h-auto rounded-lg mx-auto"
			/>
		</div>
		
		<!-- Announcement Section -->
		<div class="flex flex-col items-center gap-6 px-6 py-8 sm:px-10 sm:py-10 rounded-3xl shadow-xl backdrop-blur-sm" style="background-color: rgba(255, 255, 255, 0.9);">
			<div class="flex flex-col items-center gap-4">
				<!-- Icon or emoji -->
				<div class="text-6xl" aria-hidden="true">
					💕
				</div>
				
				<!-- Main heading -->
				<h1 class="text-2xl md:text-3xl font-bold" style="color: var(--secondary-color);">
					Registrations Are Closed
				</h1>
				
				<!-- Message -->
				<p class="text-lg md:text-xl font-semibold max-w-xl" style="color: var(--primary-color);">
					Sorry, sign-ups for this round have ended.
				</p>

				<p class="text-base md:text-lg max-w-xl" style="color: var(--secondary-color);">
					We're now matching everyone who registered. Keep an eye out for the next round!
				</p>
			</div>
			
			<!-- Additional decorative element -->
			<div class="flex items-center gap-3 mt-4">
				<div class="animate-pulse">
					<img src="/images/heart.webp" alt="" width="300" height="294" decoding="async" class="w-8 h-auto" />
				</div>
				<p class="text-sm font-semibold italic" style="color: var(--secondary-color);">
					Stay tuned for the big reveal!
				</p>
				<div class="animate-pulse">
					<img src="/images/heart.webp" alt="" width="300" height="294" decoding="async" class="w-8 h-auto" />
				</div>
			</div>
		</div>
	</div>
</div>
