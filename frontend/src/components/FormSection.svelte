<script>
  import FormField from './FormField.svelte'

  let { step, answers = {}, activeFieldName = null, currentStep, disabled = false, onUpdate } = $props()

  const STEP_ORDER = ['profile', 'food', 'anime', 'done']

  const sectionState = $derived.by(() => {
    const currentIdx = STEP_ORDER.indexOf(currentStep)
    const stepIdx = STEP_ORDER.indexOf(step.key)
    if (stepIdx < currentIdx) return 'completed'
    if (stepIdx === currentIdx) return 'current'
    return 'pending'
  })

  const stepNumber = $derived(STEP_ORDER.indexOf(step.key) + 1)
</script>

<section class="mb-4">
  <div class="flex items-center gap-2 mb-2 px-1">
    {#if sectionState === 'completed'}
      <div class="w-5 h-5 rounded-full flex items-center justify-center bg-sage text-white shrink-0">
        <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
        </svg>
      </div>
      <span class="text-sm text-sage font-medium">{step.label}</span>
    {:else if sectionState === 'current'}
      <div class="w-5 h-5 rounded-full flex items-center justify-center bg-amber text-white text-[10px] font-medium shrink-0">
        {stepNumber}
      </div>
      <span class="text-sm text-ink font-medium">{step.label}</span>
    {:else}
      <div class="w-5 h-5 rounded-full flex items-center justify-center bg-ink/5 text-ink-tertiary text-[10px] font-medium shrink-0">
        {stepNumber}
      </div>
      <span class="text-sm text-ink-tertiary">{step.label}</span>
    {/if}
  </div>

  <div class="space-y-1">
    {#each step.fields as fieldDef}
      <FormField
        {fieldDef}
        value={answers[fieldDef.key] ?? null}
        isActive={activeFieldName === fieldDef.key}
        {disabled}
        {onUpdate}
      />
    {/each}
  </div>
</section>
