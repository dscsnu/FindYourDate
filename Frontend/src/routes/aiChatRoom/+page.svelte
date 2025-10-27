<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { authStore } from '$lib/stores/auth';
	import { API_BASE_URL } from '$lib/api';
	import SignOutButton from '$lib/components/SignOutButton.svelte';

	let session = $state(null);
	let loading = $state(true);
	let userEmail = $state(null);
	let chatHistory = $state([]);
	let messages = $state([]);
	let messageIdCounter = $state(1);
	let newMessage = $state('');
	let isTyping = $state(false);
	let isComplete = $state(false);
	let currentQuestion = $state(null);
	let questionNumber = $state(0);
	let messagesContainer = $state(null);

	// Subscribe to auth store
	authStore.subscribe(value => {
		session = value;
	});

	// Auto-scroll to bottom when messages change
	$effect(() => {
		if (messages.length > 0 && messagesContainer) {
			setTimeout(() => {
				messagesContainer.scrollTop = messagesContainer.scrollHeight;
			}, 100);
		}
	});

	onMount(async () => {
		// Load session if exists
		await authStore.loadSession();
		
		// Check if user is authenticated
		const currentSession = await new Promise(resolve => {
			const unsubscribe = authStore.subscribe(value => {
				resolve(value);
				unsubscribe();
			});
		});
		
		if (!currentSession?.authenticated) {
			// Redirect to home if not authenticated
			goto('/');
			return;
		}

		userEmail = currentSession.user.email;

		// Check user status
		try {
			const response = await fetch(`${API_BASE_URL}/status/user-status?email=${encodeURIComponent(userEmail)}`, {
				credentials: 'include'
			});

			if (response.ok) {
				const data = await response.json();
				
				if (data.redirect_to === 'form') {
					// User hasn't completed form yet
					goto('/userForm');
					return;
				} else if (data.redirect_to === 'complete') {
					// User has already completed chat
					sessionStorage.setItem('user_id', data.user_id);
					goto('/endScreen');
					return;
				}
				// If redirect_to === 'chat', stay on this page
				sessionStorage.setItem('user_id', data.user_id);
			}
		} catch (error) {
			console.error('Error checking user status:', error);
		}

		loading = false;

		// Fetch first question
		await fetchNextQuestion();
	});

	async function fetchNextQuestion() {
		isTyping = true;
		
		try {
			const response = await fetch(`${API_BASE_URL}/chat/next-question`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
				},
				body: JSON.stringify({
					user_email: userEmail,
					chat_history: chatHistory
				})
			});

			if (response.status === 429) {
				// Rate limited
				const errorData = await response.json();
				isTyping = false;
				
				messages = [...messages, {
					id: messageIdCounter++,
					text: `⚠️ ${errorData.detail.message || 'Too many requests. Please wait a moment before continuing.'}`,
					sender: 'ai'
				}];
				return;
			}

			if (!response.ok) {
				throw new Error('Failed to fetch question');
			}

			const data = await response.json();
			
			isTyping = false;
			
			if (data.is_complete) {
				// Questionnaire complete
				isComplete = true;
				
				// Add completion message
				messages = [...messages, {
					id: messageIdCounter++,
					text: data.message || "Questionnaire complete! Profile created and ready to find matches.",
					sender: 'ai'
				}];

				// Show embedding status
				if (data.embedding_status === 'success') {
					messages = [...messages, {
						id: messageIdCounter++,
						text: `✅ Successfully processed ${data.answers_processed} answers and created your matching profile!`,
						sender: 'ai'
					}];
					
					// Redirect to end screen after 3 seconds
					setTimeout(() => {
						goto('/endScreen');
					}, 3000);
				} else if (data.embedding_error) {
					messages = [...messages, {
						id: messageIdCounter++,
						text: `⚠️ There was an issue creating your profile: ${data.embedding_error}`,
						sender: 'ai'
					}];
				}
			} else {
				// New question received
				currentQuestion = data.question;
				questionNumber = data.question_number;
				
				// Add question to UI
				messages = [...messages, {
					id: messageIdCounter++,
					text: data.question,
					sender: 'ai'
				}];
			}
		} catch (error) {
			isTyping = false;
			console.error('Error fetching question:', error);
			
			// Show error message
			messages = [...messages, {
				id: messageIdCounter++,
				text: "Sorry, there was an error. Please try again.",
				sender: 'ai'
			}];
		}
	}

	async function sendMessage() {
		if (!newMessage.trim() || isComplete) return;
		
		const userAnswer = newMessage.trim();
		
		// Add user message to UI
		messages = [...messages, {
			id: messageIdCounter++,
			text: userAnswer,
			sender: 'user'
		}];
		
		// Add to chat history
		chatHistory = [...chatHistory, {
			q: currentQuestion,
			a: userAnswer
		}];
		
		// Clear input
		newMessage = '';
		
		// Fetch next question
		await fetchNextQuestion();
	}

	function handleKeypress(event) {
		if (event.key === 'Enter' && !event.shiftKey) {
			event.preventDefault();
			sendMessage();
		}
	}

</script>

{#if loading}
	<div class="min-h-screen flex items-center justify-center" style="background-color: var(--primary-color);">
		<div class="text-center">
			<div class="w-16 h-16 border-4 border-white border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
			<p class="text-xl font-semibold text-white" style="font-family: 'Nunito', sans-serif;">
				Loading chat...
			</p>
		</div>
	</div>
{:else}
<div class="chat-container" style="background-color: var(--primary-color);">
	<!-- Chat Header -->
	<div class="chat-header" style="background: linear-gradient(135deg, var(--primary-color) 0%, #c54285 100%);">
		<div class="max-w-5xl mx-auto px-4 py-5 flex items-center justify-between gap-4">
			<img 
				src="/images/logo.png" 
				alt="Find Your Date" 
				class="h-14 w-auto object-contain shrink-0"
			/>
			
			<!-- q counter badge - more prominent -->
			{#if questionNumber > 0 && !isComplete}
				<div class="question-badge">
					<div class="flex items-center gap-2">
						<svg class="w-5 h-5 sm:w-6 sm:h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
						</svg>
						<div class="flex flex-col items-start">
							<span class="text-xs opacity-90 leading-none">Question</span>
							<span class="text-2xl font-bold leading-none">{questionNumber}/10</span>
						</div>
					</div>
				</div>
			{/if}
			
			<SignOutButton />
		</div>
		
		<!-- prog bar -->
		{#if questionNumber > 0 && !isComplete}
			<div class="progress-container">
				<div class="progress-bar" style="width: {(questionNumber / 10) * 100}%"></div>
			</div>
		{/if}
	</div>

	<!-- Chat Messages Container -->
	<div bind:this={messagesContainer} class="chat-messages px-4 py-6" style="background: white; border-radius: 20px 20px 0 0;">
		<div class="max-w-5xl mx-auto space-y-4">
			{#each messages as message (message.id)}
				<div class="flex {message.sender === 'user' ? 'justify-end' : 'justify-start'}">
					<div class="flex items-end gap-2 max-w-[70%] {message.sender === 'user' ? 'flex-row-reverse' : 'flex-row'}">
						
						<!-- Message Bubble -->
						<div class="flex flex-col {message.sender === 'user' ? 'items-end' : 'items-start'}">
							<div 
								class="rounded-2xl px-4 py-3 shadow-sm"
								style="{message.sender === 'user' 
									? `background-color: var(--primary-color); color: white;` 
									: 'background-color: #F1F1F3; color: var(--secondary-color);'} font-family: 'Nunito', sans-serif;"
							>
								<p class="text-sm md:text-base">{message.text}</p>
							</div>
						</div>
					</div>
				</div>
			{/each}

			<!-- Typing Indicator -->
			{#if isTyping}
				<div class="flex justify-start">
					<div class="flex items-end gap-2 max-w-[70%]">
						<div class="flex flex-col items-start">
							<div 
								class="rounded-2xl px-4 py-3 shadow-sm typing-indicator"
								style="background-color: #F1F1F3;"
							>
								<div class="flex gap-1">
									<div class="dot"></div>
									<div class="dot"></div>
									<div class="dot"></div>
								</div>
							</div>
						</div>
					</div>
				</div>
			{/if}
		</div>
	</div>

	<!-- Message Input Area -->
	<div class="chat-input bg-white shadow-lg">
		<div class="max-w-5xl mx-auto px-4 py-4">
			<form onsubmit={(e) => { e.preventDefault(); sendMessage(); }} class="flex items-center gap-3">
				<div class="flex-1">
					<textarea
						bind:value={newMessage}
						onkeypress={handleKeypress}
						placeholder="Type your message..."
						rows="1"
						class="w-full px-4 py-3 rounded-full resize-none focus:ring-2 focus:border-transparent outline-none transition-all"
						style="border: 1px solid var(--secondary-color); font-family: 'Nunito', sans-serif; max-height: 120px;"
					></textarea>
				</div>
				<!-- svelte-ignore a11y_consider_explicit_label -->
				<button
					type="submit"
					class="px-6 py-3 rounded-full text-white font-medium hover:opacity-90 transition-all duration-200 shrink-0"
					style="background-color: var(--primary-color); font-family: 'Nunito', sans-serif;"
				>
					<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/>
					</svg>
				</button>
			</form>
		</div>
	</div>
</div>
{/if}

<style>
	.chat-container {
		height: 100vh;
		height: 100dvh; /* Use dynamic viewport height for mobile keyboards */
		display: flex;
		flex-direction: column;
		overflow: hidden;
		position: relative;
	}

	.chat-header {
		flex-shrink: 0;
		position: sticky;
		top: 0;
		z-index: 100;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
	}

	/* q badge styling */
	.question-badge {
		background: rgba(255, 255, 255, 0.25);
		backdrop-filter: blur(10px);
		border: 2px solid rgba(255, 255, 255, 0.4);
		border-radius: 16px;
		padding: 0.75rem 1.25rem;
		color: white;
		font-family: 'Nunito', sans-serif;
		box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
		transition: all 0.3s ease;
	}

	.question-badge:hover {
		background: rgba(255, 255, 255, 0.35);
		transform: translateY(-2px);
		box-shadow: 0 6px 15px rgba(0, 0, 0, 0.15);
	}

	/* prog bar container */
	.progress-container {
		width: 100%;
		height: 4px;
		background: rgba(255, 255, 255, 0.2);
		position: relative;
		overflow: hidden;
	}

	/* prog bar fill */
	.progress-bar {
		height: 100%;
		background: linear-gradient(90deg, #ffffff 0%, #ffe6f0 100%);
		transition: width 0.5s ease-in-out;
		box-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
	}

	.chat-messages {
		flex: 1;
		overflow-y: auto;
		scrollbar-width: thin;
		scrollbar-color: var(--primary-color) transparent;
		min-height: 0; /* Important for flex scrolling */
	}
	
	.chat-messages::-webkit-scrollbar {
		width: 6px;
	}
	
	.chat-messages::-webkit-scrollbar-track {
		background: transparent;
	}
	
	.chat-messages::-webkit-scrollbar-thumb {
		background-color: var(--primary-color);
		border-radius: 3px;
	}

	.chat-input {
		flex-shrink: 0;
		position: sticky;
		bottom: 0;
		z-index: 100;
	}
	
	textarea {
		scrollbar-width: thin;
	}

	.typing-indicator .dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		background-color: var(--secondary-color);
		opacity: 0.4;
		animation: typingDot 1.4s infinite;
	}

	.typing-indicator .dot:nth-child(1) {
		animation-delay: 0s;
	}

	.typing-indicator .dot:nth-child(2) {
		animation-delay: 0.2s;
	}

	.typing-indicator .dot:nth-child(3) {
		animation-delay: 0.4s;
	}

	@keyframes typingDot {
		0%, 60%, 100% {
			opacity: 0.4;
			transform: translateY(0);
		}
		30% {
			opacity: 1;
			transform: translateY(-10px);
		}
	}
</style>