<script>
  import { STEPS } from '../lib/fieldDefinitions.js'
  import FormSection from './FormSection.svelte'

  let {
    onboardingState = {},
    activeFieldName = null,
    currentStep = 'profile',
    open = false,
    onToggle,
    disabled = false,
    onFieldUpdate,
  } = $props()
</script>

<!-- Mobile toggle button -->
<button
  type="button"
  onclick={onToggle}
  class="lg:hidden fixed bottom-20 right-4 z-40 w-11 h-11 rounded-full bg-amber text-white shadow-lg flex items-center justify-center hover:bg-amber-hover active:scale-95 transition cursor-pointer"
  aria-label="Toggle answers panel"
>
  <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
    {#if open}
      <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
    {:else}
      <path stroke-linecap="round" stroke-linejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
    {/if}
  </svg>
</button>

<!-- Mobile backdrop -->
{#if open}
  <div
    class="lg:hidden fixed inset-0 bg-ink/20 z-40"
    onclick={onToggle}
    role="presentation"
  ></div>
{/if}

<!-- Panel -->
<aside
  class="
    bg-surface border-l border-ink/8 flex flex-col min-h-0
    {open ? 'fixed inset-y-0 right-0 z-50 w-80' : 'hidden'}
    lg:relative lg:flex lg:z-auto lg:w-80 lg:shrink-0
  "
>
  <div class="px-4 py-4 border-b border-ink/8">
    <h2 class="font-serif text-base tracking-tight">Your Answers</h2>
  </div>

  <div id="panel-scroll" class="flex-1 overflow-y-auto px-3 py-4">
    {#each STEPS as step}
      <FormSection
        {step}
        answers={onboardingState[step.key] ?? {}}
        {activeFieldName}
        {currentStep}
        {disabled}
        onUpdate={onFieldUpdate}
      />
    {/each}
  </div>
</aside>
