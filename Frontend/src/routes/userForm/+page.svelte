<script lang="ts">
	import { goto, preloadCode } from "$app/navigation";
	import { onMount } from 'svelte';
	import { fade, fly } from 'svelte/transition';
	import { cubicOut } from 'svelte/easing';
	import { get } from 'svelte/store';
	import { authStore } from '$lib/stores/auth';

	type Session = { user: { id: string; email: string; name: string | null } | null; authenticated: boolean };
	import { api } from '$lib/api';
	import SignOutButton from '$lib/components/SignOutButton.svelte';
	import { configStore } from '$lib/stores/config';
	import { fadeIn, preloadImages } from '$lib/actions/fadeIn';
	import LoadingScreen from '$lib/components/LoadingScreen.svelte';
	import { deriveOrientation } from '$lib/orientation';

	let session = $state<Session | null>(null);
	let loading = $state(true);
	let submitting = $state(false);
    let round1ResultPublished = $state(false);

	// Subscribe to auth store
	authStore.subscribe(value => {
		session = value;
	});

	onMount(async () => {
		// Load session if exists
		await authStore.loadSession();

		const currentSession = get(authStore);

		if (!currentSession?.authenticated) {
			// Redirect to home if not authenticated
			goto('/');
			return;
		}

		round1ResultPublished = get(configStore).round1ResultPublished;

		// Check user status - if they've already completed form, redirect accordingly
		try {
			const data = await api.status.userStatus();

			if (data.redirect_to === 'chat') {
				// User has completed form but not chat
				sessionStorage.setItem('user_id', data.user_id);
				goto('/aiChatRoom');
				return;
			} else if (data.redirect_to === 'complete') {
				// User has completed everything
				sessionStorage.setItem('user_id', data.user_id);
				goto('/endScreen');
				return;
			}
			// If redirect_to === 'form', stay on this page
		} catch (error) {
			console.error('Error checking user status:', error);
			// If check fails, let them fill the form
		}
		
		loading = false;

		// Warm every option icon so stepping through the form never waits on images,
		// and fetch the chat page's code before the user needs it.
		preloadImages(Object.values(ICONS));
		preloadCode('/aiChatRoom');
	});

	const ICONS = {
		male: '/icons/male-icon.webp',
		female: '/icons/female-icon.webp',
		bisexual: '/icons/bisexual-icon.webp',
		younger: '/icons/younger-icon.webp',
		older: '/icons/older-icon.webp',
		'no-preference': '/icons/no-preference-icon.webp'
	};

	let formData = $state({
		gender: '',
		interestedIn: '', // 'men' | 'women' | 'everyone'
		agePreference: '',
		age: 21,
		mobileNumber: '',
		consentToShare: false
	});
	
	// Current step tracker
	let currentStep = $state(0);
	const totalSteps = 5; // Updated to 5 steps (removed bisexual preference question)

	// Screen state: intro -> form -> outro
	let showIntro = $state(true);
	let showOutro = $state(false);
	let showForm = $state(true);

	// Inline validation message (replaces blocking alert popups)
	let stepError = $state('');
	// 1 when moving forward, -1 when going back; drives the slide direction
	let direction = $state(1);

	function fail(message: string) {
		stepError = message;
		return false;
	}

	// Clear the error as soon as the user changes their answer
	$effect(() => {
		formData.gender; formData.interestedIn; formData.agePreference;
		formData.age; formData.mobileNumber; formData.consentToShare;
		stepError = '';
	});

	function nextStep() {
		if (currentStep < totalSteps - 1) {
			if (validateCurrentStep()) {
				direction = 1;
				currentStep++;
			}
		}
	}

	function previousStep() {
		if (currentStep > 0) {
			stepError = '';
			direction = -1;
			currentStep--;
		}
	}

	function validateCurrentStep() {
		switch(currentStep) {
			case 0:
				if (!formData.gender) {
					return fail('Please select your gender');
				}
				return true;
			case 1:
				if (!formData.interestedIn) {
					return fail('Please select who you are interested in');
				}
				return true;
			case 2:
				if (!formData.agePreference) {
					return fail('Please select your age preference');
				}
				return true;
			case 3:
				if (!formData.age) {
					return fail('Please select your age');
				}
				if (formData.age < 17 || formData.age > 25) {
					return fail('Please select an age between 17 and 25');
				}
				return true;
			case 4:
				if (!formData.mobileNumber) {
					return fail('Please enter your mobile number');
				}
				if (!/^\d{10}$/.test(formData.mobileNumber)) {
					return fail('Please enter a valid 10-digit mobile number');
				}
				if (!formData.consentToShare) {
					return fail('Please consent to share your number with your potential prom partner');
				}
				return true;
			default:
				return true;
		}
	}

	function handleSubmit() {
		if (submitting) return;
		if (validateCurrentStep()) {
			submitting = true;
			
			// Create user in backend
			createUser();
		}
	}

	async function createUser() {
		try {
			if (!session?.user) {
				throw new Error('No authenticated user');
			}

			// Map frontend form data to backend user model. The email comes
			// from the session cookie on the server, not from here.
			const suffix = round1ResultPublished ? '_ROUND2' : '';
			const userData = {
				name: (session.user.name || session.user.email) + suffix,
				phone: formData.mobileNumber,
				gender: formData.gender === 'male' ? 'M' : 'W',
				orientation: deriveOrientation(formData.gender, formData.interestedIn),
				age: formData.age,
				accept_non_straight: true, // Always accept bisexual partners
				age_preference: formData.agePreference === 'older' ? 1 : (formData.agePreference === 'younger' ? -1 : 0)
			};

			const createdUser = await api.users.create(userData);

			// Store user ID in session storage for later use
			sessionStorage.setItem('user_id', createdUser.id);

			// The form slides away and the outro fades in (see transitions below)
			showForm = false;
			showOutro = true;
			submitting = false;

		} catch (error) {
			console.error('Error creating user:', error);
			stepError = error instanceof Error ? error.message : 'Failed to create user. Please try again.';
			submitting = false;
		}
	}

	function startForm() {
		showIntro = false;
	}

	function beginChat() {
		goto('/aiChatRoom');
	}
</script>

{#snippet optionCard(selected: boolean, onSelect: () => void, icon: string, label: string)}
	<button
		type="button"
		onclick={onSelect}
		aria-pressed={selected}
		class="option-card flex flex-col items-center justify-start gap-2 sm:gap-3 p-3 sm:p-5 rounded-2xl border-2"
		class:is-selected={selected}
		style="border-color: {selected ? 'var(--secondary-color)' : '#e5e7eb'}; background-color: {selected ? 'rgba(236, 167, 186, 0.1)' : 'white'};"
	>
		<img
			src={icon}
			alt=""
			width="192"
			height="192"
			decoding="async"
			use:fadeIn
			class="w-14 h-14 sm:w-20 sm:h-20 object-contain"
		/>
		<span class="text-sm sm:text-base font-semibold leading-tight text-center" style="color: var(--secondary-color);">
			{label}
		</span>
	</button>
{/snippet}

<div class="min-h-dvh flex flex-col" style="background-color: var(--primary-color);">
	<!-- Sign Out Button - Top Right -->
	{#if !loading}
		<div class="absolute top-4 right-4 z-50">
			<SignOutButton />
		</div>
	{/if}

	<!-- Loading Screen -->
	{#if loading}
		<LoadingScreen />
	{:else}
	<!-- Intro, form and outro share one grid cell so they cross-fade without layout jumps -->
	<div class="stage flex-1">
	{#if showIntro}
		<!-- Intro Screen -->
		<section class="flex items-center justify-center px-6 py-20" out:fade={{ duration: 200 }}>
			<div class="text-center space-y-8 max-w-2xl">
				<h1 class="text-3xl md:text-4xl lg:text-5xl font-bold text-white text-balance lg:leading-tight">
					Answer a few quick questions to help us understand your preferences better.
				</h1>
				<button
					onclick={startForm}
					class="cta px-8 py-4 rounded-full text-lg font-semibold shadow-lg"
					style="background-color: white; color: var(--secondary-color);"
				>
					Start 'em
				</button>
			</div>
		</section>
	{:else if showForm}
		<!-- Form -->
		<section
			class="flex flex-col"
			in:fly={{ y: 80, duration: 600, delay: 150, easing: cubicOut }}
			out:fly={{ y: 160, duration: 450, easing: cubicOut }}
		>
			<!-- Progress Indicator -->
			<div class="py-6" role="progressbar" aria-valuemin="1" aria-valuemax={totalSteps} aria-valuenow={currentStep + 1} aria-label="Question {currentStep + 1} of {totalSteps}">
				<div class="flex justify-center gap-2 sm:gap-3">
					{#each Array(totalSteps) as _, i}
						<div 
							class="progress-dot h-2.5 sm:h-3 rounded-full"
							class:is-current={i === currentStep}
							style="background-color: {i <= currentStep ? 'white' : 'rgba(255, 255, 255, 0.5)'};"
						></div>
					{/each}
				</div>
			</div>

			<!-- Logo + card: stacked (card docked to the bottom) on mobile, side by side on desktop -->
			<div class="flex-1 flex flex-col lg:flex-row items-center justify-end lg:justify-center lg:gap-16 lg:px-12 lg:pb-12">
				<div class="w-full lg:w-auto flex items-center justify-center px-4 pb-4 lg:p-0 lg:flex-1 lg:max-w-sm">
					<img 
						src="/images/logo.webp" 
						alt="Find Your Date" 
						width="900"
						height="900"
						use:fadeIn
						class="h-40 sm:h-48 lg:h-auto w-auto lg:w-full object-contain drop-shadow-lg"
					/>
				</div>

				<!-- Form Section -->
				<div class="w-full lg:max-w-xl lg:flex-1 bg-white rounded-t-3xl lg:rounded-3xl shadow-2xl">
					<div class="p-6 sm:p-10">
					<div class="min-h-[380px] sm:min-h-[400px] flex flex-col">
					{#key currentStep}
					<div class="flex-1 flex flex-col" in:fly={{ x: 40 * direction, duration: 300, easing: cubicOut }}>
					<!-- Step 0: Gender -->
					{#if currentStep === 0}
						<div class="space-y-6 flex-1 flex flex-col justify-center">
							<h2 class="text-xl sm:text-2xl font-bold text-center text-balance" style="color: var(--secondary-color);">
								What is your gender?
							</h2>
							<div class="grid grid-cols-2 gap-4 sm:gap-6 w-full max-w-xs sm:max-w-sm mx-auto">
								{@render optionCard(formData.gender === 'male', () => formData.gender = 'male', ICONS.male, 'Male')}
								{@render optionCard(formData.gender === 'female', () => formData.gender = 'female', ICONS.female, 'Female')}
							</div>
						</div>
					{/if}

					<!-- Step 1: Who they're interested in (orientation is derived from this + gender) -->
					{#if currentStep === 1}
						<div class="space-y-6 flex-1 flex flex-col justify-center">
							<h2 class="text-xl sm:text-2xl font-bold text-center text-balance" style="color: var(--secondary-color);">
								Who are you interested in?
							</h2>
							<div class="grid grid-cols-3 gap-3 sm:gap-4 w-full max-w-md mx-auto">
								{@render optionCard(formData.interestedIn === 'men', () => formData.interestedIn = 'men', ICONS.male, 'Men')}
								{@render optionCard(formData.interestedIn === 'women', () => formData.interestedIn = 'women', ICONS.female, 'Women')}
								{@render optionCard(formData.interestedIn === 'everyone', () => formData.interestedIn = 'everyone', ICONS.bisexual, 'Everyone')}
							</div>
						</div>
					{/if}

					<!-- Step 2: Age Preference -->
					{#if currentStep === 2}
						<div class="space-y-6 flex-1 flex flex-col justify-center">
							<h2 class="text-xl sm:text-2xl font-bold text-center text-balance" style="color: var(--secondary-color);">
								Would you prefer to be matched with someone older or younger than you?
							</h2>
							<div class="grid grid-cols-3 gap-3 sm:gap-4 w-full max-w-md mx-auto">
								{@render optionCard(formData.agePreference === 'younger', () => formData.agePreference = 'younger', ICONS.younger, 'Younger')}
								{@render optionCard(formData.agePreference === 'older', () => formData.agePreference = 'older', ICONS.older, 'Older')}
								{@render optionCard(formData.agePreference === 'no-preference', () => formData.agePreference = 'no-preference', ICONS['no-preference'], 'No Preference')}
							</div>
						</div>
					{/if}

					<!-- Step 3: Age -->
					{#if currentStep === 3}
						<div class="space-y-6 flex-1 flex flex-col justify-center">
							<h2 class="text-xl sm:text-2xl font-bold text-center text-balance" style="color: var(--secondary-color);">
								<label for="age">What is your age?</label>
							</h2>
							<div class="max-w-lg mx-auto w-full">
								<div class="relative px-6 sm:px-8 py-8 rounded-2xl" style="background: linear-gradient(135deg, rgba(236, 167, 186, 0.1), rgba(236, 167, 186, 0.05));">
									<input 
										id="age"
										type="range" 
										bind:value={formData.age}
										min="17" 
										max="25"
										class="w-full age-slider"
										style="background: linear-gradient(to right, var(--primary-color) 0%, var(--primary-color) {((formData.age - 17) / (25 - 17)) * 100}%, rgba(236, 167, 186, 0.2) {((formData.age - 17) / (25 - 17)) * 100}%, rgba(236, 167, 186, 0.2) 100%);"
									/>
									<div class="mt-6 text-center">
										<div class="inline-block px-6 py-3 rounded-full shadow-md" style="background-color: var(--primary-color);">
											<span class="text-4xl font-bold text-white tabular-nums">
												{formData.age}
											</span>
										</div>
									</div>
								</div>
							</div>
						</div>
					{/if}

					<!-- Step 4: Mobile Number -->
					{#if currentStep === 4}
						<div class="space-y-6 flex-1 flex flex-col justify-center">
							<h2 class="text-xl sm:text-2xl font-bold text-center text-balance" style="color: var(--secondary-color);">
								<label for="mobile">Please enter your mobile number so that your prom match can reach you?</label>
							</h2>
							<div class="max-w-md mx-auto w-full space-y-4">
								<input 
									id="mobile"
									type="tel" 
									inputmode="numeric"
									autocomplete="tel-national"
									bind:value={formData.mobileNumber}
									placeholder="Enter 10-digit mobile number"
									maxlength="10"
									pattern="[0-9]{10}"
									class="w-full px-6 py-4 text-lg rounded-2xl border-2 transition-colors duration-200 focus:outline-none text-center font-semibold tracking-wide"
									style="border-color: {formData.mobileNumber ? 'var(--secondary-color)' : '#e5e7eb'}; color: var(--secondary-color);"
									oninput={(e) => {
										// Only allow digits
										const target = e.target;
										if (target && target instanceof HTMLInputElement) {
											formData.mobileNumber = target.value.replace(/\D/g, '');
										}
									}}
									onkeydown={(e) => { if (e.key === 'Enter') handleSubmit(); }}
								/>
								<div class="flex items-start gap-3 p-4 rounded-xl" style="background-color: rgba(236, 167, 186, 0.1);">
									<input 
										type="checkbox" 
										id="consent"
										bind:checked={formData.consentToShare}
										class="mt-1 w-5 h-5 shrink-0 cursor-pointer"
										style="accent-color: var(--secondary-color);"
									/>
									<label 
										for="consent" 
										class="text-sm sm:text-base cursor-pointer select-none"
										style="color: var(--secondary-color);"
									>
										Yes, I consent to share my number with my potential prom partner
									</label>
								</div>
							</div>
						</div>
					{/if}
					</div>
					{/key}

					<!-- Inline validation / submit error -->
					<div class="min-h-6 mt-4 text-center" aria-live="assertive">
						{#if stepError}
							<p class="step-error text-sm font-semibold" style="color: var(--accent-color);" role="alert">
								{stepError}
							</p>
						{/if}
					</div>

					<!-- Navigation Buttons -->
					<div class="flex justify-between items-center mt-4">
						<!-- Left Arrow Button -->
						<button
							type="button"
							onclick={previousStep}
							disabled={currentStep === 0}
							aria-label="Previous question"
							class="nav-arrow bg-transparent border-none p-0 rounded-full disabled:opacity-30 disabled:cursor-not-allowed"
						>
							<img 
								src="/icons/arrow-icon.png" 
								alt="" 
								width="64"
								height="64"
								class="w-12 h-12 transform rotate-180"
							/>
						</button>

						<!-- Right Arrow or Submit Button -->
						{#if currentStep < totalSteps - 1}
							<button
								type="button"
								onclick={nextStep}
								aria-label="Next question"
								class="nav-arrow bg-transparent border-none p-0 rounded-full"
							>
								<img 
									src="/icons/arrow-icon.png" 
									alt="" 
									width="64"
									height="64"
									class="w-12 h-12"
								/>
							</button>
						{:else}
							<button 
								type="button"
								onclick={handleSubmit}
								disabled={submitting}
								class="cta py-3 px-8 rounded-full text-white font-semibold text-base shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
								style="background-color: var(--secondary-color);"
							>
								{#if submitting}
									<span class="flex items-center gap-2">
										<div class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
										Creating...
									</span>
								{:else}
									Submit
								{/if}
							</button>
						{/if}
					</div>
					</div>
					</div>
				</div>
			</div>
		</section>
	{:else if showOutro}
		<!-- Outro Screen -->
		<section class="flex items-center justify-center px-6 py-20" in:fade={{ duration: 400, delay: 350 }}>
			<div class="text-center space-y-8 max-w-2xl">
				<h1 class="text-3xl md:text-4xl lg:text-5xl font-bold text-white text-balance lg:leading-tight">
					Now chat with our AI for a few minutes—it'll learn your interests and vibe to find your most compatible prom match!
				</h1>
				<button
					onclick={beginChat}
					class="cta px-8 py-4 rounded-full text-lg font-semibold shadow-lg"
					style="background-color: white; color: var(--secondary-color);"
				>
					Begin!
				</button>
			</div>
		</section>
	{/if}
	</div>
	{/if}
</div>

<style>
	/* Stack every screen in one grid cell so transitions overlap in place */
	.stage {
		display: grid;
	}

	.stage > :global(section) {
		grid-area: 1 / 1;
		min-width: 0;
	}

	.cta {
		transition: transform 0.2s var(--ease-out), box-shadow 0.2s var(--ease-out), opacity 0.2s;
	}

	.cta:hover:not(:disabled) {
		transform: translateY(-2px) scale(1.03);
		box-shadow: 0 12px 24px -8px rgba(49, 48, 53, 0.35);
	}

	.cta:active:not(:disabled) {
		transform: scale(0.98);
	}

	.progress-dot {
		width: 1.25rem;
		transition: width 0.35s var(--ease-out), background-color 0.35s;
	}

	.progress-dot.is-current {
		width: 2.25rem;
	}

	@media (min-width: 640px) {
		.progress-dot {
			width: 2.5rem;
		}

		.progress-dot.is-current {
			width: 4rem;
		}
	}

	.option-card {
		transition: transform 0.2s var(--ease-out), box-shadow 0.2s var(--ease-out),
			border-color 0.2s, background-color 0.2s;
	}

	.option-card:hover {
		transform: translateY(-3px);
		box-shadow: 0 10px 20px -10px rgba(236, 167, 186, 0.9);
	}

	.option-card:active {
		transform: scale(0.97);
	}

	.option-card.is-selected {
		box-shadow: 0 8px 18px -10px rgba(49, 48, 53, 0.45);
	}

	.nav-arrow {
		transition: transform 0.2s var(--ease-out), opacity 0.2s;
	}

	.nav-arrow:hover:not(:disabled) {
		transform: scale(1.08);
	}

	.nav-arrow:active:not(:disabled) {
		transform: scale(0.94);
	}

	.step-error {
		animation: shake 0.35s var(--ease-out);
	}

	@keyframes shake {
		0%, 100% { transform: translateX(0); }
		25% { transform: translateX(-6px); }
		75% { transform: translateX(6px); }
	}

	.age-slider {
		-webkit-appearance: none;
		appearance: none;
		height: 6px;
		border-radius: 10px;
		outline: none;
		box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.1);
	}

	.age-slider::-webkit-slider-thumb {
		-webkit-appearance: none;
		appearance: none;
		width: 32px;
		height: 32px;
		border-radius: 50%;
		background: linear-gradient(145deg, #f5b7c6, #ec97aa);
		cursor: pointer;
		box-shadow: 0 4px 12px rgba(236, 167, 186, 0.4), 0 2px 4px rgba(0, 0, 0, 0.1);
		transition: transform 0.2s ease, box-shadow 0.2s ease;
		border: 3px solid white;
	}

	.age-slider::-webkit-slider-thumb:hover {
		transform: scale(1.15);
		box-shadow: 0 6px 16px rgba(236, 167, 186, 0.6), 0 4px 8px rgba(0, 0, 0, 0.15);
	}

	.age-slider::-webkit-slider-thumb:active {
		transform: scale(1.05);
	}

	.age-slider::-moz-range-thumb {
		width: 32px;
		height: 32px;
		border-radius: 50%;
		background: linear-gradient(145deg, #f5b7c6, #ec97aa);
		cursor: pointer;
		border: 3px solid white;
		box-shadow: 0 4px 12px rgba(236, 167, 186, 0.4), 0 2px 4px rgba(0, 0, 0, 0.1);
		transition: transform 0.2s ease, box-shadow 0.2s ease;
	}

	.age-slider::-moz-range-thumb:hover {
		transform: scale(1.15);
		box-shadow: 0 6px 16px rgba(236, 167, 186, 0.6), 0 4px 8px rgba(0, 0, 0, 0.15);
	}

	.age-slider::-moz-range-thumb:active {
		transform: scale(1.05);
	}

	.age-slider::-moz-range-track {
		height: 8px;
		border-radius: 5px;
		background: #e5e7eb;
	}
</style>
