<script>
	let messages = [
		{ id: 1, text: "Hi! How are you?", sender: "ai" },
		{ id: 2, text: "I'm doing great! Thanks for asking.", sender: "user" },
		{ id: 3, text: "What would you like to talk about today?", sender: "ai" }
	];
	
	let newMessage = '';
	let messageIdCounter = 4;

	function scrollToBottom() {
		setTimeout(() => {
			const chatContainer = document.querySelector('.chat-messages');
			if (chatContainer) {
				chatContainer.scrollTop = chatContainer.scrollHeight;
			}
		}, 10);
	}

	function sendMessage() {
		if (newMessage.trim()) {
			messages = [...messages, {
				id: messageIdCounter++,
				text: newMessage,
				sender: 'user'
			}];
			
			newMessage = '';
			scrollToBottom();
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
			scrollToBottom();
		}
	}

	// @ts-ignore
	function handleKeypress(event) {
		if (event.key === 'Enter' && !event.shiftKey) {
			event.preventDefault();
			sendMessage();
		}
	}

</script>

<div class="chat-container">
	<!-- Chat Header -->
	<div class="chat-header bg-white border-b shadow-sm" style="border-bottom: 1px solid var(--primary-color);">
		<div class="max-w-5xl mx-auto px-4 py-4 flex items-center gap-4">
			<img 
				src="/images/cupid.png" 
				alt="AI Avatar" 
				class="w-12 h-12 object-cover"
			/>
			<div>
				<h2 class="text-xl font-bold" style="color: var(--primary-color); font-family: 'Nunito', sans-serif;">
					Snupid
				</h2>
			</div>
		</div>
	</div>

	<!-- Chat Messages Container -->
	<div class="chat-messages px-4 py-6" style="background: linear-gradient(to bottom, #faf5ff, #f3e8ff);">
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
									: 'background-color: white; color: var(--secondary-color);'} font-family: 'Nunito', sans-serif;"
							>
								<p class="text-sm md:text-base">{message.text}</p>
							</div>
						</div>
					</div>
				</div>
			{/each}
		</div>
	</div>

	<!-- Message Input Area -->
	<div class="chat-input bg-white border-t shadow-lg" style="border-top: 1px solid var(--primary-color);">
		<div class="max-w-5xl mx-auto px-4 py-4">
			<form on:submit|preventDefault={sendMessage} class="flex items-center gap-3">
				<div class="flex-1">
					<textarea
						bind:value={newMessage}
						on:keypress={handleKeypress}
						placeholder="Type your message..."
						rows="1"
						class="w-full px-4 py-3 rounded-full resize-none focus:ring-2 focus:border-transparent outline-none transition-all"
						style="border: 1px solid var(--primary-color); font-family: 'Nunito', sans-serif; max-height: 120px;"
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
</style>