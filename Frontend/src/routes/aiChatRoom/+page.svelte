<script>
	let messages = [
		{ id: 1, text: "Hi! How are you?", sender: "ai" },
		{ id: 2, text: "I'm doing great! Thanks for asking.", sender: "user" },
		{ id: 3, text: "What would you like to talk about today?", sender: "ai" }
	];
	
	let newMessage = '';
	let messageIdCounter = 4;
	let isTyping = false;

	function sendMessage() {
		if (newMessage.trim()) {
			messages = [...messages, {
				id: messageIdCounter++,
				text: newMessage,
				sender: 'user'
			}];
			
			newMessage = '';
		}
	}

	// @ts-ignore
	function sendAIMessage(text) {
		if (text && text.trim()) {
			messages = [...messages, {
				id: messageIdCounter++,
				text: text.trim(),
				sender: 'ai'
			}];
		}
	}

	// @ts-ignore
	function handleKeypress(event) {
		if (event.key === 'Enter' && !event.shiftKey) {
			event.preventDefault();
			sendMessage();
		}
	}

	function showTypingIndicator() {
		isTyping = true;
	}

	function hideTypingIndicator() {
		isTyping = false;
	}
	showTypingIndicator();

// To hide it
hideTypingIndicator();

// Example: Show typing, wait 5 seconds, then show AI message
showTypingIndicator();
setTimeout(() => {
    hideTypingIndicator();
    sendAIMessage("Here's my response!");
}, 5000);


</script>

<div class="chat-container" style="background-color: var(--primary-color);">
	<!-- Chat Header -->
	<div class="chat-header" style="background-color: var(--primary-color); height: 80px;">
		<div class="max-w-5xl mx-auto px-4 py-4 flex items-center gap-4 h-full">
			<h1 class="text-white text-2xl font-bold" style="font-family: 'Nunito', sans-serif;">
				Find Your Date
			</h1>
		</div>
		
	</div>

	<!-- Chat Messages Container -->
	<div class="chat-messages px-4 py-6" style="background: white; border-radius: 20px 20px 0 0;">
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
			<form on:submit|preventDefault={sendMessage} class="flex items-center gap-3">
				<div class="flex-1">
					<textarea
						bind:value={newMessage}
						on:keypress={handleKeypress}
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

<style>
	.chat-container {
		height: 100vh;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}

	.chat-header {
		flex-shrink: 0;
	}

	.chat-messages {
		flex: 1;
		overflow-y: auto;
		scrollbar-width: thin;
		scrollbar-color: var(--primary-color) transparent;
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