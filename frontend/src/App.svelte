<script>
  import { tick } from 'svelte'
  import { sendMessage } from './lib/api.js'
  import StepProgress from './components/StepProgress.svelte'
  import ChatMessage from './components/ChatMessage.svelte'
  import ChatInput from './components/ChatInput.svelte'
  import SourceList from './components/SourceList.svelte'
  import TypingIndicator from './components/TypingIndicator.svelte'

  let messages = $state([])
  let sessionId = $state(null)
  let currentStep = $state('profile')
  let isLoading = $state(false)
  let messagesEl
  let chatInputEl

  async function scrollToBottom() {
    await tick()
    if (messagesEl) {
      messagesEl.scrollTop = messagesEl.scrollHeight
    }
  }

  async function handleSend(text) {
    messages.push({ role: 'user', text })
    isLoading = true
    await scrollToBottom()

    try {
      const data = await sendMessage(text, sessionId)
      sessionId = data.session_id
      currentStep = data.state.current_step
      messages.push({
        role: 'assistant',
        text: data.response.message,
        sources: data.response.sources,
      })
    } catch (err) {
      messages.push({ role: 'assistant', text: 'Error: ' + err.message, isError: true })
    } finally {
      isLoading = false
      await scrollToBottom()
      chatInputEl?.focus()
    }
  }
</script>

<div class="bg-gray-100 h-screen flex flex-col">
  <header class="bg-white shadow px-6 py-4">
    <h1 class="text-xl font-semibold text-gray-800 mb-3">Conversation Agent</h1>
    <StepProgress {currentStep} />
  </header>

  <main class="flex-1 overflow-hidden flex flex-col max-w-3xl w-full mx-auto">
    <div id="messages" bind:this={messagesEl} class="flex-1 overflow-y-auto p-4 space-y-4">
      {#each messages as msg}
        <ChatMessage role={msg.role} text={msg.text} isError={msg.isError} />
        {#if msg.sources}
          <SourceList sources={msg.sources} />
        {/if}
      {/each}
      {#if isLoading}
        <TypingIndicator />
      {/if}
    </div>

    <ChatInput onSend={handleSend} disabled={isLoading} bind:this={chatInputEl} />
  </main>
</div>
