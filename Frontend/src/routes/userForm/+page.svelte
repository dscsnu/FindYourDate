<script>
	let formData = {
		gender: '',
		sexuality: '',
		preferredPartnerSexuality: '',
		comfortableWithNonStraight: null,
		age: ''
	};

	// You can replace this with actual username from authentication
	let username = "Gopal !";

	function handleSubmit() {
		if (formData.comfortableWithNonStraight === null) {
			alert('Please answer whether you are comfortable with a non-straight partner');
			return;
		}
		console.log('Form submitted:', formData);
		// Handle form submission logic here
	}
</script>

<div class="min-h-screen flex items-center justify-center px-4 py-8">
	<div class="flex flex-col lg:flex-row items-center justify-center gap-8 lg:gap-16 max-w-6xl w-full">
		<!-- Logo Section - Only visible on large screens -->
		<div class="hidden lg:flex flex-col items-center shrink-0">
			<img 
				src="/images/logo.png" 
				alt="Find Your Date Logo" 
				class="max-w-sm w-full h-auto rounded-lg mb-4"
			/>
			<h3 class="text-2xl font-bold" style="color: var(--primary-color); font-family: 'Nunito', sans-serif;">
				Hello {username}
			</h3>
		</div>

		<!-- Form Section -->
		<div class="w-full max-w-xl bg-transparent rounded-2xl p-8">
		<h2 class="text-2xl font-bold text-center mb-8" style="color: var(--primary-color); font-family: 'Nunito', sans-serif;">
			Complete Your Profile
		</h2>
		
		<form on:submit|preventDefault={handleSubmit} class="space-y-6">
			<!-- Gender Field -->
			<div class="space-y-2">
				<label for="gender" class="flex items-center gap-2 text-sm font-medium" style="color: var(--secondary-color); font-family: 'Nunito', sans-serif;">
					<img src="/icons/gender-icon.png" alt="Gender" class="w-4 h-4" />
					Gender
				</label>
				<select 
					id="gender"
					bind:value={formData.gender}
					class="w-full p-3 rounded-lg focus:ring-2 focus:border-transparent outline-none transition-all"
					style="border: 1px solid var(--primary-color); focus:ring-color: var(--primary-color);"
					required
				>
					<option value="male">Male</option>
					<option value="female">Female</option>
					<option value="non-binary">Non-binary</option>
				</select>
			</div>

			<!-- Sexuality Fields - Side by Side -->
			<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
				<!-- Your Sexuality Field -->
				<div class="space-y-2">
					<label for="sexuality" class="flex items-center gap-2 text-sm font-medium" style="color: var(--secondary-color); font-family: 'Nunito', sans-serif;">
						<img src="/icons/sexuality-icon.png" alt="Sexuality" class="w-4 h-4" />
						Your Sexuality
					</label>
					<select 
						id="sexuality"
						bind:value={formData.sexuality}
						class="w-full p-3 rounded-lg focus:ring-2 focus:border-transparent outline-none transition-all"
						style="border: 1px solid var(--primary-color); focus:ring-color: var(--primary-color);"
						required
					>
						<option value="straight">Straight</option>
						<option value="gay">Gay</option>
						<option value="lesbian">Lesbian</option>
					</select>
				</div>

				<!-- Preferred Partner's Sexuality -->
				<div class="space-y-2">
					<label for="preferredSexuality" class="flex items-center gap-2 text-sm font-medium whitespace-nowrap" style="color: var(--secondary-color); font-family: 'Nunito', sans-serif;">
						<img src="/icons/sexuality-icon.png" alt="Sexuality" class="w-4 h-4" />
						Preferred Partner's Sexuality
					</label>
					<select 
						id="preferredSexuality"
						bind:value={formData.preferredPartnerSexuality}
						class="w-full p-3 rounded-lg focus:ring-2 focus:border-transparent outline-none transition-all"
						style="border: 1px solid var(--primary-color); focus:ring-color: var(--primary-color);"
						required
					>
						<option value="straight">Straight</option>
						<option value="gay">Gay</option>
						<option value="lesbian">Lesbian</option>
						<option value="bisexual">Bisexual</option>
					</select>
				</div>
			</div>

			<!-- Comfortable with Non-Straight Partner -->
			<div class="space-y-3">
				<fieldset>
					<legend class="block text-sm font-medium" style="color: var(--secondary-color); font-family: 'Nunito', sans-serif;">
						Are you comfortable with a non-straight partner?
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
						<span class="text-sm" style="color: var(--secondary-color); font-family: 'Nunito', sans-serif;">Yes</span>
					</label>
					<label class="flex items-center">
						<input 
							type="radio" 
							bind:group={formData.comfortableWithNonStraight} 
							value={false}
							class="mr-3 focus:ring-purple-500"
							style="accent-color: var(--primary-color); border: 1px solid var(--primary-color);"
						/>
						<span class="text-sm" style="color: var(--secondary-color); font-family: 'Nunito', sans-serif;">No</span>
					</label>
				</div>
				</fieldset>
			</div>

			<!-- Age Field -->
			<div class="space-y-2">
				<label for="age" class="block text-sm font-medium" style="color: var(--secondary-color); font-family: 'Nunito', sans-serif;">
					Age
				</label>
				<input 
					id="age"
					type="number" 
					bind:value={formData.age}
					min="18" 
					max="29"
					class="w-full p-3 rounded-lg focus:ring-2 focus:border-transparent outline-none transition-all"
					style="border: 1px solid var(--primary-color); focus:ring-color: var(--primary-color);"
					required
				/>
			</div>

			<!-- Submit Button -->
			<button 
				type="submit"
				class="w-full py-3 px-6 rounded-lg text-white font-medium text-base hover:opacity-90 transition-all duration-200 mt-8"
				style="background-color: var(--primary-color); font-family: 'Nunito', sans-serif;"
			>
				Continue
			</button>
		</form>
	</div>
	</div>
</div>