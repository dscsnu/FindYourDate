<script>
  import { goto } from "$app/navigation";

	function signInWithGoogle() {
		goto('/userForm');
	}
</script>

<div class="flex items-center justify-center min-h-screen px-4">
	<div class="flex flex-col lg:flex-row items-center justify-center gap-8 lg:gap-16 max-w-6xl w-full">
		<!-- Image Section -->
		<div class="shrink-0">
			<img 
				src="/images/logo.png" 
				alt="Find Your Date placeholder" 
				class="max-w-md w-full h-auto rounded-lg"
			/>
		</div>
		
		<!-- Text and Button Section -->
		<div class="text-center lg:text-left flex flex-col items-center lg:items-start">
			<p class="text-lg md:text-xl font-bold mb-6 max-w-md" style="color: var(--secondary-color); font-family: 'Nunito', sans-serif;">
				Find your ideal prom date! 
				Tell us who you are, 
				and let our AI match you with your perfect vibe.
			</p>
			<button onclick={signInWithGoogle} 
				class="flex items-center justify-center gap-3 px-6 py-3 bg-white border border-gray-300 rounded-full text-gray-700 font-medium text-base hover:bg-gray-50 hover:border-gray-400 transition-all duration-200"
				style="font-family: 'Montserrat', sans-serif;"
			>
				<svg width="20" height="20" viewBox="0 0 24 24">
					<path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
					<path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
					<path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
					<path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
				</svg>
				Sign in with Google
			</button>
			<div class="ml-2 mt-3 flex items-center gap-2">
				<img src="/icons/information-icon.png" alt="Info" class="w-4 h-4" />
				<p class="text-sm font-semibold" style="color: white; font-family: 'Nunito', sans-serif;">
					Sign in with your SNU mail ID
				</p>
			</div>
		</div>
	</div>
</div>