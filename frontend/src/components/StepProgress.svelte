<script>
  const STEPS = ['profile', 'food', 'anime']
  const STEP_ORDER = [...STEPS, 'done']
  const LABELS = { profile: '1. Profile', food: '2. Food', anime: '3. Anime' }

  let { currentStep } = $props()

  function stepClasses(step) {
    const currentIdx = STEP_ORDER.indexOf(currentStep)
    const stepIdx = STEP_ORDER.indexOf(step)

    const base = 'px-3 py-1 rounded-full text-sm font-medium border'

    if (stepIdx < currentIdx) {
      return `${base} bg-green-100 text-green-700 border-green-300`
    } else if (stepIdx === currentIdx) {
      return `${base} bg-blue-100 text-blue-700 border-blue-300`
    } else {
      return `${base} bg-gray-100 text-gray-500 border-gray-300`
    }
  }
</script>

<div class="flex gap-2">
  {#each STEPS as step}
    <div class={stepClasses(step)}>{LABELS[step]}</div>
  {/each}
</div>
