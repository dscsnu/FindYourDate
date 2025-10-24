<script>
    import { goto } from "$app/navigation";

	let formData = {
		gender: '',
		sexuality: '',
		preferredPartnerSexuality: '',
		comfortableWithNonStraight: null,
		age: ''
	};

	// You can replace this with actual username from authentication
	let username = "Gopal !";
	
	// Current step tracker
	let currentStep = 0;
	const totalSteps = 5; // Updated to 5 steps

	function nextStep() {
		if (currentStep < totalSteps - 1) {
			if (validateCurrentStep()) {
				currentStep++;
			}
		}
	}

	function previousStep() {
		if (currentStep > 0) {
			currentStep--;
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
				if (!formData.preferredPartnerSexuality) {
					alert('Please select preferred partner\'s sexuality');
					return false;
				}
				return true;
			case 3:
				if (formData.comfortableWithNonStraight === null) {
					alert('Please answer whether you are comfortable with a non-straight partner');
					return false;
				}
				return true;
			case 4:
				if (!formData.age) {
					alert('Please enter your age');
					return false;
				}
				if (parseInt(formData.age) < 18 || parseInt(formData.age) > 30) {
					alert('Please enter an age between 18 and 30');
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

	<!-- Content Container - Image and Form -->
	<div class="flex-1 flex flex-col lg:flex-row lg:items-center lg:justify-center lg:gap-8 lg:px-8 lg:max-w-7xl lg:mx-auto lg:w-full">
		<!-- Image Section -->
		<div class="flex-1 flex items-center justify-center px-4 lg:px-0 lg:max-w-md">
			<img 
				src="/placeholderImage.png" 
				alt="Form illustration" 
				class="max-w-md w-full h-auto object-contain"
				style="max-height: 225px;"
			/>
		</div>

		<!-- Form Section -->
		<div class="w-full lg:w-auto lg:flex-1 lg:max-w-xl bg-white rounded-t-3xl lg:rounded-3xl shadow-2xl">
			<div class="p-8">
			<div class="min-h-[300px] flex flex-col">
			<!-- Step 0: Gender -->
			{#if currentStep === 0}
				<div class="space-y-2 flex-1">
					<label for="gender" class="block text-lg font-bold" style="color: var(--secondary-color); font-family: 'Nunito', sans-serif;">
						What's Your Gender?
					</label>
					<select 
						id="gender"
						bind:value={formData.gender}
						class="w-full p-3 rounded-lg focus:ring-2 focus:border-transparent outline-none transition-all"
						style="border: 1px solid var(--primary-color); focus:ring-color: var(--primary-color);"
					>
						<option value="male">Male</option>
						<option value="female">Female</option>
						<option value="non-binary">Non-binary</option>
					</select>
				</div>
			{/if}

			<!-- Step 1: Your Sexuality -->
			{#if currentStep === 1}
				<div class="space-y-2 flex-1">
					<label for="sexuality" class="block text-lg font-bold" style="color: var(--secondary-color); font-family: 'Nunito', sans-serif;">
						What's Your Sexuality?
					</label>
					<select 
						id="sexuality"
						bind:value={formData.sexuality}
						class="w-full p-3 rounded-lg focus:ring-2 focus:border-transparent outline-none transition-all"
						style="border: 1px solid var(--primary-color); focus:ring-color: var(--primary-color);"
					>
						<option value="straight">Straight</option>
						<option value="gay">Gay</option>
						<option value="lesbian">Lesbian</option>
					</select>
				</div>
			{/if}

			<!-- Step 2: Preferred Partner's Sexuality -->
			{#if currentStep === 2}
				<div class="space-y-2 flex-1">
					<label for="preferredSexuality" class="block text-lg font-bold" style="color: var(--secondary-color); font-family: 'Nunito', sans-serif;">
						You'd like to be Matched with a?
					</label>
					<select 
						id="preferredSexuality"
						bind:value={formData.preferredPartnerSexuality}
						class="w-full p-3 rounded-lg focus:ring-2 focus:border-transparent outline-none transition-all"
						style="border: 1px solid var(--primary-color); focus:ring-color: var(--primary-color);"
					>
						<option value="straight">Straight</option>
						<option value="gay">Gay</option>
						<option value="lesbian">Lesbian</option>
						<option value="bisexual">Bisexual</option>
					</select>
				</div>
			{/if}

			<!-- Step 3: Comfortable with Non-Straight Partner -->
			{#if currentStep === 3}
				<div class="space-y-3 flex-1">
					<fieldset>
						<legend class="block text-lg font-bold mb-4" style="color: var(--secondary-color); font-family: 'Nunito', sans-serif;">
							Would you be open to being matched with someone who isn't straight?
						</legend>
					<div class="space-y-2">
						<label class="flex items-center">
							<input 
								type="radio" 
								bind:group={formData.comfortableWithNonStraight} 
								value={true}
								class="mr-3 focus:ring-purple-500"
								style="accent-color: var(--primary-color); border: 1px solid var(--primary-color);"
							/>
							<span class="text-sm" style="color: var(--secondary-color); font-family: 'Nunito', sans-serif;">
								Yes, I'm open to it
							</span>
						</label>
						<label class="flex items-center">
							<input 
								type="radio" 
								bind:group={formData.comfortableWithNonStraight} 
								value={false}
								class="mr-3 focus:ring-purple-500"
								style="accent-color: var(--primary-color); border: 1px solid var(--primary-color);"
							/>
							<span class="text-sm" style="color: var(--secondary-color); font-family: 'Nunito', sans-serif;">
								No, I prefer a straight partner
							</span>
						</label>
					</div>
					</fieldset>
				</div>
			{/if}

			<!-- Step 4: Age -->
			{#if currentStep === 4}
				<div class="space-y-2 flex-1">
					<label for="age" class="block text-lg font-bold" style="color: var(--secondary-color); font-family: 'Nunito', sans-serif;">
						What's Your Age?
					</label>
					<input 
						id="age"
						type="number" 
						bind:value={formData.age}
						min="18" 
						max="30"
						class="w-full p-3 rounded-lg focus:ring-2 focus:border-transparent outline-none transition-all"
						style="border: 1px solid var(--primary-color); focus:ring-color: var(--primary-color);"
						placeholder="Enter your age"
					/>
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
</style>
	</div>
</div>