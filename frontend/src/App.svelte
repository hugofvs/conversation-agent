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
  let activeQuestion = $state(null)
  let messagesEl
  let chatInputEl

  async function scrollToBottom() {
    await tick()
    if (messagesEl) {
      messagesEl.scrollTop = messagesEl.scrollHeight
    }
  }

  async function handleSend(text) {
    activeQuestion = null
    messages.push({ role: 'user', text })
    isLoading = true
    await scrollToBottom()

    try {
      const data = await sendMessage(text, sessionId)
      sessionId = data.session_id
      currentStep = data.state.current_step
      activeQuestion = data.response.next_question ?? null
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

<div class="bg-canvas min-h-screen flex flex-col">
  <header class="bg-surface border-b border-ink/8 px-6 py-5">
    <div class="max-w-3xl mx-auto">
      <h1 class="font-serif text-xl tracking-tight mb-4">Conversation Agent</h1>
      <StepProgress {currentStep} />
    </div>
  </header>

  <main class="flex-1 flex flex-col max-w-3xl w-full mx-auto">
    <div id="messages" bind:this={messagesEl} class="flex-1 overflow-y-auto px-6 py-8 space-y-5">
      {#if messages.length === 0 && !isLoading}
        <div class="flex-1 flex items-center justify-center h-full">
          <div class="text-center">
            <p class="font-serif text-lg text-ink/70">Tell me about yourself.</p>
            <p class="text-sm text-ink-tertiary mt-2">Three chapters — profile, food, anime.</p>
          </div>
        </div>
      {/if}
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

    <ChatInput onSend={handleSend} disabled={isLoading} {activeQuestion} bind:this={chatInputEl} />
  </main>
</div>
