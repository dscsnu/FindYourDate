<script lang="ts">
	import { onMount, tick } from 'svelte';
	import { fly } from 'svelte/transition';
	import { cubicOut } from 'svelte/easing';
	import { goto, preloadCode } from '$app/navigation';
	import { get } from 'svelte/store';
	import { authStore } from '$lib/stores/auth';
	import { api } from '$lib/api';
	import SignOutButton from '$lib/components/SignOutButton.svelte';
	import LoadingScreen from '$lib/components/LoadingScreen.svelte';

	type ChatMessage = { id: number; text: string; sender: 'ai' | 'user' };
	type QA = { q: string; a: string };

	let session = $state<{ user: { email: string } | null; authenticated: boolean } | null>(null);
	let loading = $state(true);
	let userEmail = $state<string | null>(null);
	let chatHistory = $state<QA[]>([]);
	let messages = $state<ChatMessage[]>([]);
	let messageIdCounter = $state(1);
	let newMessage = $state('');
	let isTyping = $state(false);
	let isComplete = $state(false);
	let currentQuestion = $state<string | null>(null);
	let questionNumber = $state(0);
	let messagesContainer = $state<HTMLDivElement | null>(null);
	let inputEl = $state<HTMLTextAreaElement | null>(null);
	let retryAvailable = $state(false);

	// Subscribe to auth store
	authStore.subscribe(value => {
		session = value;
	});

	// Load chat from localStorage
	function loadChatFromStorage() {
		if (typeof window === 'undefined') return;
		
		const savedChat = localStorage.getItem(`chat_${userEmail}`);
		if (savedChat) {
			try {
				const parsed = JSON.parse(savedChat);
				chatHistory = parsed.chatHistory || [];
				messages = parsed.messages || [];
				messageIdCounter = parsed.messageIdCounter || 1;
				currentQuestion = parsed.currentQuestion || null;
				questionNumber = parsed.questionNumber || 0;
				isComplete = parsed.isComplete || false;
			} catch (e) {
				console.error('Error loading chat from storage:', e);
			}
		}
	}

	// Save chat to localStorage
	function saveChatToStorage() {
		if (typeof window === 'undefined' || !userEmail) return;
		
		const chatData = {
			chatHistory,
			messages,
			messageIdCounter,
			currentQuestion,
			questionNumber,
			isComplete
		};
		localStorage.setItem(`chat_${userEmail}`, JSON.stringify(chatData));
	}

	// Auto-save when chat data changes
	$effect(() => {
		if (userEmail && (messages.length > 0 || chatHistory.length > 0)) {
			saveChatToStorage();
		}
	});

	// Keep the newest message in view; smooth once the chat is on screen
	let hasScrolled = false;
	$effect(() => {
		messages.length;
		isTyping;
		retryAvailable;
		if (!messagesContainer) return;
		tick().then(() => {
			if (!messagesContainer) return;
			messagesContainer.scrollTo({
				top: messagesContainer.scrollHeight,
				behavior: hasScrolled ? 'smooth' : 'instant'
			});
			hasScrolled = true;
		});
	});

	// Grow the input with its content (capped by max-height in CSS)
	$effect(() => {
		newMessage;
		if (!inputEl) return;
		inputEl.style.height = 'auto';
		inputEl.style.height = `${inputEl.scrollHeight}px`;
	});

	// Restart chat function
	function restartChat() {
		if (!confirm('Are you sure you want to restart the chat? All progress will be lost.')) {
			return;
		}
		
		// Clear localStorage
		if (typeof window !== 'undefined' && userEmail) {
			localStorage.removeItem(`chat_${userEmail}`);
		}
		
		// Reset all state
		chatHistory = [];
		messages = [];
		messageIdCounter = 1;
		currentQuestion = null;
		questionNumber = 0;
		isComplete = false;
		newMessage = '';
		
		// Fetch first question again
		fetchNextQuestion();
	}

	onMount(async () => {
		// Load session if exists
		await authStore.loadSession();

		const currentSession = get(authStore);

		if (!currentSession?.authenticated) {
			// Redirect to home if not authenticated
			goto('/');
			return;
		}

		userEmail = currentSession.user?.email ?? null;

		// Check user status
		try {
			const data = await api.status.userStatus();

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
		} catch (error) {
			console.error('Error checking user status:', error);
		}

		loading = false;

		// Load saved chat from localStorage
		loadChatFromStorage();

		// Fetch first question only if no saved chat
		if (messages.length === 0 && !isComplete) {
			await fetchNextQuestion();
		}
	});

	const RETRY_DELAYS_MS = [1500, 4000, 9000];

	async function fetchNextQuestion(attempt = 0) {
		isTyping = true;

		try {
			const response = await api.chat.nextQuestion(chatHistory);

			// 503 means the server's LLM queue is full. It clears, so wait and
			// retry rather than dead-ending the user mid-questionnaire.
			if (response.status === 503 && attempt < RETRY_DELAYS_MS.length) {
				await new Promise((r) => setTimeout(r, RETRY_DELAYS_MS[attempt]));
				return fetchNextQuestion(attempt + 1);
			}

			if (response.status === 429 || response.status === 503) {
				const errorData = await response.json().catch(() => ({}));
				isTyping = false;

				messages = [...messages, {
					id: messageIdCounter++,
					text: `⚠️ ${errorData?.detail?.message || 'We are busy right now. Please wait a moment and try again.'}`,
					sender: 'ai'
				}];
				retryAvailable = true;
				return;
			}

			if (!response.ok) {
				throw new Error('Failed to fetch question');
			}

			retryAvailable = false;

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
					preloadCode('/endScreen');
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

			messages = [...messages, {
				id: messageIdCounter++,
				text: "Sorry, there was an error. Please try again.",
				sender: 'ai'
			}];
			retryAvailable = true;
		}
	}

	function retryQuestion() {
		retryAvailable = false;
		fetchNextQuestion();
	}

	async function sendMessage() {
		if (!newMessage.trim() || isComplete || isTyping) return;

		const userAnswer = newMessage.trim();
		
		// Add user message to UI
		messages = [...messages, {
			id: messageIdCounter++,
			text: userAnswer,
			sender: 'user'
		}];
		
		// Add to chat history
		chatHistory = [...chatHistory, {
			q: currentQuestion as string,
			a: userAnswer
		}];
		
		// Clear input
		newMessage = '';
		
		// Fetch next question
		await fetchNextQuestion();
		inputEl?.focus({ preventScroll: true });
	}

	function handleKeypress(event: KeyboardEvent) {
		if (event.key === 'Enter' && !event.shiftKey) {
			event.preventDefault();
			sendMessage();
		}
	}

</script>

{#if loading}
	<LoadingScreen message="Loading chat..." />
{:else}
<div class="chat-container" style="background-color: var(--primary-color);">
	<!-- Chat Header -->
	<header class="chat-header" style="background: linear-gradient(135deg, var(--primary-color) 0%, var(--accent-color) 100%);">
		<div class="max-w-[52rem] mx-auto px-3 sm:px-6 py-3 sm:py-4 flex items-center justify-between gap-3">
			<img 
				src="/images/logo.webp" 
				alt="Find Your Date" 
				width="900"
				height="900"
				class="h-11 sm:h-14 w-auto object-contain shrink-0"
			/>

			<div class="flex items-center gap-2 sm:gap-3 min-w-0">
				<!-- q counter badge - more prominent -->
				{#if questionNumber > 0 && !isComplete}
					<div class="question-badge" aria-live="polite">
						<div class="flex items-center gap-2">
							<svg class="hidden sm:block w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
							</svg>
							<div class="flex flex-col items-start">
								<span class="text-[10px] sm:text-xs opacity-90 leading-none">Question</span>
								<span class="text-lg sm:text-2xl font-bold leading-none tabular-nums">{questionNumber}/10</span>
							</div>
						</div>
					</div>
				{/if}
				{#if messages.length > 0 && !isComplete}
					<button
						onclick={restartChat}
						class="text-white text-xs sm:text-sm font-semibold px-3 py-1.5 sm:py-2 rounded-full border border-white/80 hover:bg-white hover:text-[var(--accent-color)] transition-colors duration-200 whitespace-nowrap"
						title="Restart chat"
					>
						Restart
					</button>
				{/if}
				<SignOutButton />
			</div>
		</div>
		
		<!-- prog bar -->
		<div class="progress-container" class:is-hidden={!(questionNumber > 0 && !isComplete)}>
			<div class="progress-bar" style="transform: scaleX({isComplete ? 1 : questionNumber / 10})"></div>
		</div>
	</header>

	<!-- Chat panel: full-bleed sheet on mobile, centered card on desktop -->
	<div class="chat-panel">
		<!-- Chat Messages Container -->
		<div bind:this={messagesContainer} class="chat-messages px-4 sm:px-6 py-6" aria-live="polite">
			<div class="space-y-3 sm:space-y-4">
				{#each messages as message (message.id)}
					<div
						class="flex {message.sender === 'user' ? 'justify-end' : 'justify-start'}"
						in:fly={{ y: 12, duration: 300, easing: cubicOut }}
					>
						<div 
							class="bubble max-w-[85%] sm:max-w-[75%] rounded-2xl px-4 py-3 shadow-sm {message.sender === 'user' ? 'rounded-br-md' : 'rounded-bl-md'}"
							style="{message.sender === 'user' 
								? `background-color: var(--primary-color); color: white;` 
								: 'background-color: #F1F1F3; color: var(--secondary-color);'}"
						>
							<p class="text-[15px] md:text-base leading-relaxed whitespace-pre-wrap break-words">{message.text}</p>
						</div>
					</div>
				{/each}

				{#if retryAvailable && !isTyping}
					<div class="flex justify-start" in:fly={{ y: 8, duration: 250 }}>
						<button
							onclick={retryQuestion}
							class="rounded-full px-5 py-2 text-sm font-semibold text-white transition-opacity duration-200 hover:opacity-90"
							style="background-color: var(--primary-color);"
						>
							Try again
						</button>
					</div>
				{/if}

				<!-- Typing Indicator -->
				{#if isTyping}
					<div class="flex justify-start" in:fly={{ y: 8, duration: 250 }} role="status" aria-label="Thinking">
						<div 
							class="rounded-2xl rounded-bl-md px-4 py-4 shadow-sm typing-indicator"
							style="background-color: #F1F1F3;"
						>
							<div class="flex gap-1">
								<div class="dot"></div>
								<div class="dot"></div>
								<div class="dot"></div>
							</div>
						</div>
					</div>
				{/if}
			</div>
		</div>

		<!-- Message Input Area -->
		<div class="chat-input">
			<form onsubmit={(e) => { e.preventDefault(); sendMessage(); }} class="flex items-end gap-2 sm:gap-3">
				<textarea
					bind:this={inputEl}
					bind:value={newMessage}
					onkeydown={handleKeypress}
					disabled={isTyping || isComplete}
					placeholder={isTyping ? 'Thinking...' : 'Type your message...'}
					aria-label="Your answer"
					rows="1"
					class="flex-1 min-w-0 px-5 py-3 rounded-3xl resize-none outline-none transition-shadow duration-200 disabled:bg-gray-50"
				></textarea>
				<button
					type="submit"
					disabled={isTyping || isComplete || !newMessage.trim()}
					aria-label="Send message"
					class="send-btn h-12 w-12 sm:w-auto sm:px-6 flex items-center justify-center rounded-full text-white shrink-0 disabled:opacity-50 disabled:cursor-not-allowed"
					style="background-color: var(--primary-color);"
				>
					<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
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
		-webkit-backdrop-filter: blur(10px);
		border: 2px solid rgba(255, 255, 255, 0.4);
		border-radius: 14px;
		padding: 0.4rem 0.75rem;
		color: white;
		box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
	}

	@media (min-width: 640px) {
		.question-badge {
			border-radius: 16px;
			padding: 0.6rem 1.1rem;
		}
	}

	/* prog bar container */
	.progress-container {
		width: 100%;
		height: 4px;
		background: rgba(255, 255, 255, 0.2);
		position: relative;
		overflow: hidden;
		transition: opacity 0.3s;
	}

	.progress-container.is-hidden {
		opacity: 0;
	}

	/* prog bar fill: scaleX animates on the compositor, unlike width */
	.progress-bar {
		height: 100%;
		width: 100%;
		transform-origin: left center;
		background: linear-gradient(90deg, #ffffff 0%, #ffe6f0 100%);
		transition: transform 0.6s var(--ease-out);
		box-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
	}

	.chat-panel {
		flex: 1;
		min-height: 0; /* Important for flex scrolling */
		width: 100%;
		max-width: 52rem;
		margin: 0 auto;
		display: flex;
		flex-direction: column;
		background: white;
		border-radius: 20px 20px 0 0;
		overflow: hidden;
		margin-top: 0.75rem;
	}

	/* Desktop: a floating card with breathing room instead of an edge-to-edge sheet */
	@media (min-width: 1024px) {
		.chat-panel {
			margin: 1.5rem auto;
			border-radius: 28px;
			box-shadow: 0 30px 60px -20px rgba(49, 48, 53, 0.35);
		}
	}

	.chat-messages {
		flex: 1;
		overflow-y: auto;
		overscroll-behavior: contain;
		-webkit-overflow-scrolling: touch;
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
		padding: 0.75rem 1rem;
		padding-bottom: max(0.75rem, env(safe-area-inset-bottom));
		border-top: 1px solid #f1f1f3;
		background: white;
	}

	@media (min-width: 640px) {
		.chat-input {
			padding: 1rem 1.5rem;
		}
	}
	
	textarea {
		scrollbar-width: thin;
		border: 1px solid var(--secondary-color);
		max-height: 120px;
		line-height: 1.5;
	}

	textarea:focus,
	textarea:focus-visible {
		outline: none;
		box-shadow: 0 0 0 3px rgba(236, 167, 186, 0.6);
	}

	.send-btn {
		transition: transform 0.2s var(--ease-out), opacity 0.2s;
	}

	.send-btn:hover:not(:disabled) {
		transform: scale(1.05);
	}

	.send-btn:active:not(:disabled) {
		transform: scale(0.95);
	}

	.bubble {
		overflow-wrap: anywhere;
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
			transform: translateY(-6px);
		}
	}
</style>
