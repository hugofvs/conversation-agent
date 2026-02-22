<script>
  import { tick } from 'svelte'
  import { sendMessage } from './lib/api.js'
  import { patchState } from './lib/stateApi.js'
  import StepProgress from './components/StepProgress.svelte'
  import ChatMessage from './components/ChatMessage.svelte'
  import ChatInput from './components/ChatInput.svelte'
  import SourceList from './components/SourceList.svelte'
  import TypingIndicator from './components/TypingIndicator.svelte'
  import SidePanel from './components/SidePanel.svelte'

  let messages = $state([])
  let sessionId = $state(null)
  let currentStep = $state('profile')
  let isLoading = $state(false)
  let activeQuestion = $state(null)
  let onboardingState = $state({ profile: {}, food: {}, anime: {} })
  let panelOpen = $state(false)
  let messagesEl
  let chatInputEl

  const activeFieldName = $derived(activeQuestion?.field_name ?? null)

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
      onboardingState = {
        profile: data.state.profile ?? onboardingState.profile,
        food: data.state.food ?? onboardingState.food,
        anime: data.state.anime ?? onboardingState.anime,
      }
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

  async function handleFieldUpdate(fieldName, value) {
    if (!sessionId) return
    try {
      const resp = await patchState(sessionId, { [fieldName]: value })
      currentStep = resp.state.current_step
      onboardingState = {
        profile: resp.state.profile,
        food: resp.state.food,
        anime: resp.state.anime,
      }
      activeQuestion = resp.next_question ?? null
    } catch (err) {
      console.error('Failed to update field:', err)
    }
  }
</script>

<div class="bg-canvas min-h-screen flex flex-col">
  <header class="bg-surface border-b border-ink/8 px-6 py-5">
    <div class="max-w-3xl mx-auto lg:max-w-none">
      <h1 class="font-serif text-xl tracking-tight mb-4">Conversation Agent</h1>
      <StepProgress {currentStep} />
    </div>
  </header>

  <div class="flex-1 flex min-h-0">
    <main class="flex-1 flex flex-col min-w-0">
      <div id="messages" bind:this={messagesEl} class="flex-1 overflow-y-auto px-6 py-8 space-y-5">
        <div class="max-w-3xl mx-auto w-full space-y-5">
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
      </div>

      <ChatInput onSend={handleSend} disabled={isLoading} {activeQuestion} bind:this={chatInputEl} />
    </main>

    <SidePanel
      {onboardingState}
      {activeFieldName}
      {currentStep}
      open={panelOpen}
      onToggle={() => panelOpen = !panelOpen}
      disabled={isLoading}
      onFieldUpdate={handleFieldUpdate}
    />
  </div>
</div>
