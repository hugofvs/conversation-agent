<script>
  const STEPS = ['profile', 'food', 'anime']
  const STEP_ORDER = [...STEPS, 'done']
  const LABELS = { profile: 'Profile', food: 'Food', anime: 'Anime' }

  let { currentStep } = $props()

  function getState(step) {
    const currentIdx = STEP_ORDER.indexOf(currentStep)
    const stepIdx = STEP_ORDER.indexOf(step)
    if (stepIdx < currentIdx) return 'completed'
    if (stepIdx === currentIdx) return 'current'
    return 'pending'
  }
</script>

<div class="flex items-center">
  {#each STEPS as step, i}
    {@const state = getState(step)}
    <div class="flex items-center">
      <div class="flex items-center gap-2.5">
        {#if state === 'completed'}
          <div class="w-6 h-6 rounded-full flex items-center justify-center bg-sage text-white">
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <span class="text-sm text-sage font-medium">{LABELS[step]}</span>
        {:else if state === 'current'}
          <div class="w-6 h-6 rounded-full flex items-center justify-center bg-amber text-white text-xs font-medium">
            {i + 1}
          </div>
          <span class="text-sm text-ink font-medium">{LABELS[step]}</span>
        {:else}
          <div class="w-6 h-6 rounded-full flex items-center justify-center bg-ink/5 text-ink-tertiary text-xs font-medium">
            {i + 1}
          </div>
          <span class="text-sm text-ink-tertiary">{LABELS[step]}</span>
        {/if}
      </div>

      {#if i < STEPS.length - 1}
        {@const connectorDone = getState(STEPS[i]) === 'completed'}
        <div class="w-10 h-px mx-3 {connectorDone ? 'bg-sage/30' : 'bg-ink/8'}"></div>
      {/if}
    </div>
  {/each}
</div>
