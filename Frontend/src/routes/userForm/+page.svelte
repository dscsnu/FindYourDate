<script>
    import { goto } from "$app/navigation";

	let formData = {
		gender: '',
		sexuality: '',
		comfortableWithNonStraight: null,
		agePreference: '',
		age: 21
	};

	// You can replace this with actual username from authentication
	let username = "Gopal !";
	
	// Current step tracker
	let currentStep = 0;
	const totalSteps = 5; // Updated to 5 steps

	function nextStep() {
		if (currentStep < totalSteps - 1) {
			if (validateCurrentStep()) {
				// Skip step 2 (comfortableWithNonStraight) if user is not straight
				if (currentStep === 1 && formData.sexuality !== 'straight') {
					currentStep += 2; // Skip to age preference question
				} else {
					currentStep++;
				}
			}
		}
	}

	function previousStep() {
		if (currentStep > 0) {
			// Skip step 2 (comfortableWithNonStraight) if user is not straight
			if (currentStep === 3 && formData.sexuality !== 'straight') {
				currentStep -= 2; // Go back to sexuality question
			} else {
				currentStep--;
			}
		}
	}

	function validateCurrentStep() {
		switch(currentStep) {
			case 0:
				if (!formData.gender) {
					alert('Please select your gender');
					return false;
				}
				return true;
			case 1:
				if (!formData.sexuality) {
					alert('Please select your sexuality');
					return false;
				}
				return true;
			case 2:
				// Only validate if user is straight
				if (formData.sexuality === 'straight') {
					if (formData.comfortableWithNonStraight === null) {
						alert('Please answer whether you are comfortable with a non-straight partner');
						return false;
					}
				}
				return true;
			case 3:
				if (!formData.agePreference) {
					alert('Please select your age preference');
					return false;
				}
				return true;
			case 4:
				if (!formData.age) {
					alert('Please select your age');
					return false;
				}
				if (parseInt(formData.age) < 17 || parseInt(formData.age) > 25) {
					alert('Please select an age between 17 and 25');
					return false;
				}
				return true;
			default:
				return true;
		}
	}

	function handleSubmit() {
		if (validateCurrentStep()) {
			console.log('Form submitted:', formData);
			goto('/aiChatRoom');
		}
	}
</script>

<div class="min-h-screen flex flex-col" style="background-color: var(--primary-color);">
	<!-- Progress Indicator - Fixed at top -->
	<div class="py-6">
		<div class="flex justify-center gap-3">
			{#each Array(totalSteps) as _, i}
				<div 
					class="h-3 rounded-full transition-all duration-300"
					class:w-16={i === currentStep}
					class:w-10={i !== currentStep}
					style="background-color: {i <= currentStep ? 'white' : 'rgba(255, 255, 255, 0.5)'};"
				></div>
			{/each}
		</div>
	</div>

	<!-- Content Container - Form -->
	<div class="flex-1 flex items-end lg:items-center justify-center">
		<!-- Form Section -->
		<div class="w-full lg:max-w-2xl bg-white rounded-t-3xl lg:rounded-3xl shadow-2xl">
			<div class="p-10">
			<div class="min-h-[400px] flex flex-col">
			<!-- Step 0: Gender -->
			{#if currentStep === 0}
				<div class="space-y-6 flex-1 flex flex-col justify-center">
					<h2 class="text-2xl font-bold text-center" style="color: var(--secondary-color); font-family: 'Nunito', sans-serif;">
						What is your gender?
					</h2>
					<div class="flex gap-6 justify-center">
						<!-- Male Button -->
						<button
							type="button"
							on:click={() => formData.gender = 'male'}
							class="flex flex-col items-center gap-3 p-6 rounded-2xl border-2 transition-all duration-200 hover:scale-105"
							class:selected-gender={formData.gender === 'male'}
							style="border-color: {formData.gender === 'male' ? 'var(--secondary-color)' : '#e5e7eb'}; background-color: {formData.gender === 'male' ? 'rgba(236, 167, 186, 0.1)' : 'white'};"
						>
							<img 
								src="/icons/male-icon.png" 
								alt="Male" 
								class="w-24 h-24 object-contain"
							/>
							<span class="text-lg font-semibold" style="color: var(--secondary-color); font-family: 'Nunito', sans-serif;">
								Male
							</span>
						</button>

						<!-- Female Button -->
						<button
							type="button"
							on:click={() => formData.gender = 'female'}
							class="flex flex-col items-center gap-3 p-6 rounded-2xl border-2 transition-all duration-200 hover:scale-105"
							class:selected-gender={formData.gender === 'female'}
							style="border-color: {formData.gender === 'female' ? 'var(--secondary-color)' : '#e5e7eb'}; background-color: {formData.gender === 'female' ? 'rgba(236, 167, 186, 0.1)' : 'white'};"
						>
							<img 
								src="/icons/female-icon.png" 
								alt="Female" 
								class="w-24 h-24 object-contain"
							/>
							<span class="text-lg font-semibold" style="color: var(--secondary-color); font-family: 'Nunito', sans-serif;">
								Female
							</span>
						</button>
					</div>
				</div>
			{/if}

			<!-- Step 1: Your Sexuality -->
			{#if currentStep === 1}
				<div class="space-y-6 flex-1 flex flex-col justify-center">
					<h2 class="text-2xl font-bold text-center" style="color: var(--secondary-color); font-family: 'Nunito', sans-serif;">
						What's Your Sexuality?
					</h2>
					<div class="flex flex-wrap gap-4 justify-center">
						<!-- Straight Button -->
						<button
							type="button"
							on:click={() => formData.sexuality = 'straight'}
							class="flex flex-col items-center gap-3 p-4 rounded-2xl border-2 transition-all duration-200 hover:scale-105"
							style="border-color: {formData.sexuality === 'straight' ? 'var(--secondary-color)' : '#e5e7eb'}; background-color: {formData.sexuality === 'straight' ? 'rgba(236, 167, 186, 0.1)' : 'white'};"
						>
							<img 
								src="/icons/straight-icon.png" 
								alt="Straight" 
								class="w-20 h-20 object-contain"
							/>
							<span class="text-base font-semibold" style="color: var(--secondary-color); font-family: 'Nunito', sans-serif;">
								Straight
							</span>
						</button>

						<!-- Gay Button (only for males) -->
						{#if formData.gender === 'male'}
							<button
								type="button"
								on:click={() => formData.sexuality = 'gay'}
								class="flex flex-col items-center gap-3 p-4 rounded-2xl border-2 transition-all duration-200 hover:scale-105"
								style="border-color: {formData.sexuality === 'gay' ? 'var(--secondary-color)' : '#e5e7eb'}; background-color: {formData.sexuality === 'gay' ? 'rgba(236, 167, 186, 0.1)' : 'white'};"
							>
								<img 
									src="/icons/gay-icon.png" 
									alt="Gay" 
									class="w-20 h-20 object-contain"
								/>
								<span class="text-base font-semibold" style="color: var(--secondary-color); font-family: 'Nunito', sans-serif;">
									Gay
								</span>
							</button>
						{/if}

						<!-- Lesbian Button (only for females) -->
						{#if formData.gender === 'female'}
							<button
								type="button"
								on:click={() => formData.sexuality = 'lesbian'}
								class="flex flex-col items-center gap-3 p-4 rounded-2xl border-2 transition-all duration-200 hover:scale-105"
								style="border-color: {formData.sexuality === 'lesbian' ? 'var(--secondary-color)' : '#e5e7eb'}; background-color: {formData.sexuality === 'lesbian' ? 'rgba(236, 167, 186, 0.1)' : 'white'};"
							>
								<img 
									src="/icons/lesbian-icon.png" 
									alt="Lesbian" 
									class="w-20 h-20 object-contain"
								/>
								<span class="text-base font-semibold" style="color: var(--secondary-color); font-family: 'Nunito', sans-serif;">
									Lesbian
								</span>
							</button>
						{/if}

						<!-- Bisexual Button -->
						<button
							type="button"
							on:click={() => formData.sexuality = 'bisexual'}
							class="flex flex-col items-center gap-3 p-4 rounded-2xl border-2 transition-all duration-200 hover:scale-105"
							style="border-color: {formData.sexuality === 'bisexual' ? 'var(--secondary-color)' : '#e5e7eb'}; background-color: {formData.sexuality === 'bisexual' ? 'rgba(236, 167, 186, 0.1)' : 'white'};"
						>
							<img 
								src="/icons/bisexual-icon.png" 
								alt="Bisexual" 
								class="w-20 h-20 object-contain"
							/>
							<span class="text-base font-semibold" style="color: var(--secondary-color); font-family: 'Nunito', sans-serif;">
								Bisexual
							</span>
						</button>
					</div>
				</div>
			{/if}

			<!-- Step 2: Comfortable with Non-Straight Partner (only for straight users) -->
			{#if currentStep === 2 && formData.sexuality === 'straight'}
				<div class="space-y-6 flex-1 flex flex-col justify-center">
					<h2 class="text-2xl font-bold text-center" style="color: var(--secondary-color); font-family: 'Nunito', sans-serif;">
						Would you be open to being matched with someone who is bisexual?
					</h2>
					<div class="flex gap-6 justify-center">
						<!-- Yes Button -->
						<button
							type="button"
							on:click={() => formData.comfortableWithNonStraight = true}
							class="flex flex-col items-center gap-3 p-6 rounded-2xl border-2 transition-all duration-200 hover:scale-105 w-48"
							style="border-color: {formData.comfortableWithNonStraight === true ? 'var(--secondary-color)' : '#e5e7eb'}; background-color: {formData.comfortableWithNonStraight === true ? 'rgba(236, 167, 186, 0.1)' : 'white'};"
						>
							<img 
								src="/icons/thumbs-up-icon.png" 
								alt="Yes" 
								class="w-24 h-24 object-contain"
							/>
							<span class="text-base font-semibold text-center" style="color: var(--secondary-color); font-family: 'Nunito', sans-serif;">
								Yes, I'm open to it
							</span>
						</button>

						<!-- No Button -->
						<button
							type="button"
							on:click={() => formData.comfortableWithNonStraight = false}
							class="flex flex-col items-center gap-3 p-6 rounded-2xl border-2 transition-all duration-200 hover:scale-105 w-48"
							style="border-color: {formData.comfortableWithNonStraight === false ? 'var(--secondary-color)' : '#e5e7eb'}; background-color: {formData.comfortableWithNonStraight === false ? 'rgba(236, 167, 186, 0.1)' : 'white'};"
						>
							<img 
								src="/icons/thumbs-down-icon.png" 
								alt="No" 
								class="w-24 h-24 object-contain"
							/>
							<span class="text-base font-semibold text-center" style="color: var(--secondary-color); font-family: 'Nunito', sans-serif;">
								No, I prefer a straight partner
							</span>
						</button>
					</div>
				</div>
			{/if}

			<!-- Step 3: Age Preference -->
			{#if currentStep === 3}
				<div class="space-y-6 flex-1 flex flex-col justify-center">
					<h2 class="text-2xl font-bold text-center" style="color: var(--secondary-color); font-family: 'Nunito', sans-serif;">
						Would you prefer to be matched with someone older or younger than you?
					</h2>
					<div class="flex flex-wrap gap-4 justify-center">
						<!-- Younger Button -->
						<button
							type="button"
							on:click={() => formData.agePreference = 'younger'}
							class="flex flex-col items-center gap-3 p-6 rounded-2xl border-2 transition-all duration-200 hover:scale-105"
							style="border-color: {formData.agePreference === 'younger' ? 'var(--secondary-color)' : '#e5e7eb'}; background-color: {formData.agePreference === 'younger' ? 'rgba(236, 167, 186, 0.1)' : 'white'};"
						>
							<img 
								src="/icons/younger-icon.png" 
								alt="Younger" 
								class="w-20 h-20 object-contain"
							/>
							<span class="text-base font-semibold" style="color: var(--secondary-color); font-family: 'Nunito', sans-serif;">
								Younger
							</span>
						</button>

						<!-- Older Button -->
						<button
							type="button"
							on:click={() => formData.agePreference = 'older'}
							class="flex flex-col items-center gap-3 p-6 rounded-2xl border-2 transition-all duration-200 hover:scale-105"
							style="border-color: {formData.agePreference === 'older' ? 'var(--secondary-color)' : '#e5e7eb'}; background-color: {formData.agePreference === 'older' ? 'rgba(236, 167, 186, 0.1)' : 'white'};"
						>
							<img 
								src="/icons/older-icon.png" 
								alt="Older" 
								class="w-20 h-20 object-contain"
							/>
							<span class="text-base font-semibold" style="color: var(--secondary-color); font-family: 'Nunito', sans-serif;">
								Older
							</span>
						</button>

						<!-- No Preference Button -->
						<button
							type="button"
							on:click={() => formData.agePreference = 'no-preference'}
							class="flex flex-col items-center gap-3 p-6 rounded-2xl border-2 transition-all duration-200 hover:scale-105"
							style="border-color: {formData.agePreference === 'no-preference' ? 'var(--secondary-color)' : '#e5e7eb'}; background-color: {formData.agePreference === 'no-preference' ? 'rgba(236, 167, 186, 0.1)' : 'white'};"
						>
							<img 
								src="/icons/no-preference-icon.png" 
								alt="No Preference" 
								class="w-20 h-20 object-contain"
							/>
							<span class="text-base font-semibold" style="color: var(--secondary-color); font-family: 'Nunito', sans-serif;">
								No Preference
							</span>
						</button>
					</div>
				</div>
			{/if}

			<!-- Step 4: Age -->
			{#if currentStep === 4}
				<div class="space-y-6 flex-1 flex flex-col justify-center">
					<h2 class="text-2xl font-bold text-center" style="color: var(--secondary-color); font-family: 'Nunito', sans-serif;">
						What is your age?
					</h2>
					<div class="max-w-lg mx-auto w-full">
						<div class="relative px-8 py-8 rounded-2xl" style="background: linear-gradient(135deg, rgba(236, 167, 186, 0.1), rgba(236, 167, 186, 0.05));">
							<div class="flex items-center gap-8">
								<div class="flex-1 relative">
									<input 
										id="age"
										type="range" 
										bind:value={formData.age}
										min="17" 
										max="25"
										class="w-full age-slider"
										style="background: linear-gradient(to right, var(--primary-color) 0%, var(--primary-color) {((formData.age - 17) / (25 - 17)) * 100}%, rgba(236, 167, 186, 0.2) {((formData.age - 17) / (25 - 17)) * 100}%, rgba(236, 167, 186, 0.2) 100%);"
									/>
								</div>
							</div>
							<div class="mt-6 text-center">
								<div class="inline-block px-6 py-3 rounded-full shadow-md" style="background-color: var(--primary-color);">
									<span class="text-4xl font-bold text-white" style="font-family: 'Nunito', sans-serif;">
										{formData.age}
									</span>
								</div>
							</div>
						</div>
					</div>
				</div>
			{/if}

			<!-- Navigation Buttons -->
			<div class="flex justify-between items-center mt-8">
				<!-- Left Arrow Button -->
				<button
					type="button"
					on:click={previousStep}
					disabled={currentStep === 0}
					class="transition-all duration-200 bg-transparent border-none p-0 cursor-pointer"
					class:opacity-30={currentStep === 0}
					class:cursor-not-allowed={currentStep === 0}
					class:pointer-events-none={currentStep === 0}
				>
					<img 
						src="/icons/arrow-icon.png" 
						alt="Previous" 
						class="w-12 h-12 transform rotate-180"
					/>
				</button>

				<!-- Right Arrow or Submit Button -->
				{#if currentStep < totalSteps - 1}
					<button
						type="button"
						on:click={nextStep}
						class="transition-all duration-200 hover:opacity-80 bg-transparent border-none p-0 cursor-pointer"
					>
						<img 
							src="/icons/arrow-icon.png" 
							alt="Next" 
							class="w-12 h-12"
						/>
					</button>
				{:else}
					<button 
						type="button"
						on:click={handleSubmit}
						class="py-3 px-8 rounded-full text-white font-semibold text-base hover:opacity-90 transition-all duration-200 shadow-md"
						style="background-color: var(--secondary-color); font-family: 'Nunito', sans-serif;"
					>
						Submit
					</button>
				{/if}
			</div>
		</div>
	</div>
</div>

<style>
	@media (min-width: 700px) {
		/* Ensure side-by-side layout on larger screens */
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
		transition: all 0.3s ease;
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
		transition: all 0.3s ease;
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
	</div>
</div>