<script>
  let { fieldDef, value = null, isActive = false, disabled = false, onUpdate } = $props()

  function handleTextChange(e) {
    onUpdate(fieldDef.key, e.target.value)
  }

  function handleSelectChange(e) {
    const raw = e.target.value
    // spice_ok uses boolean values
    if (raw === 'true') return onUpdate(fieldDef.key, true)
    if (raw === 'false') return onUpdate(fieldDef.key, false)
    onUpdate(fieldDef.key, raw)
  }

  function handleCheckbox(optionValue, checked) {
    const current = Array.isArray(value) ? [...value] : []
    if (checked) {
      if (!current.includes(optionValue)) current.push(optionValue)
    } else {
      const idx = current.indexOf(optionValue)
      if (idx !== -1) current.splice(idx, 1)
    }
    onUpdate(fieldDef.key, current.length > 0 ? current : null)
  }

  const displayValue = $derived(
    fieldDef.type === 'list' && Array.isArray(value) ? value.join(', ') : (value ?? '')
  )

  function handleListChange(e) {
    const raw = e.target.value
    if (!raw.trim()) return onUpdate(fieldDef.key, null)
    onUpdate(fieldDef.key, raw.split(',').map(s => s.trim()).filter(Boolean))
  }
</script>

<div class="py-2 px-3 rounded-lg transition-colors {isActive ? 'bg-amber-soft ring-1 ring-amber/25' : value != null ? 'bg-sage-soft/50' : ''}">
  <!-- svelte-ignore a11y_label_has_associated_control -->
  <label class="block">
  <span class="block text-xs mb-1.5 {isActive ? 'text-amber font-medium' : 'text-ink-secondary'}">
    {#if isActive}
      <span class="inline-block w-1.5 h-1.5 rounded-full bg-amber animate-pulse mr-1 align-middle"></span>
    {/if}
    {fieldDef.label}
  </span>

  {#if fieldDef.type === 'text'}
    <input
      type="text"
      value={value ?? ''}
      {disabled}
      onchange={handleTextChange}
      placeholder="..."
      class="w-full bg-transparent border border-ink/10 rounded-md px-2.5 py-1.5 text-sm text-ink placeholder:text-ink-muted focus:outline-none focus:ring-1 focus:ring-amber/25 focus:border-amber/40 transition disabled:opacity-40"
    />

  {:else if fieldDef.type === 'list'}
    <input
      type="text"
      value={displayValue}
      {disabled}
      onchange={handleListChange}
      placeholder="Comma-separated..."
      class="w-full bg-transparent border border-ink/10 rounded-md px-2.5 py-1.5 text-sm text-ink placeholder:text-ink-muted focus:outline-none focus:ring-1 focus:ring-amber/25 focus:border-amber/40 transition disabled:opacity-40"
    />

  {:else if fieldDef.type === 'enum'}
    <select
      value={value != null ? String(value) : ''}
      {disabled}
      onchange={handleSelectChange}
      class="w-full bg-transparent border border-ink/10 rounded-md px-2.5 py-1.5 text-sm text-ink focus:outline-none focus:ring-1 focus:ring-amber/25 focus:border-amber/40 transition disabled:opacity-40 cursor-pointer"
    >
      <option value="" disabled>Select...</option>
      {#each fieldDef.options as opt}
        <option value={String(opt.value)}>{opt.label}</option>
      {/each}
    </select>

  {:else if fieldDef.type === 'multi'}
    <div class="flex flex-wrap gap-x-3 gap-y-1.5">
      {#each fieldDef.options as opt}
        {@const checked = Array.isArray(value) && value.includes(opt.value)}
        <label class="inline-flex items-center gap-1.5 text-sm text-ink-secondary cursor-pointer select-none">
          <input
            type="checkbox"
            {checked}
            {disabled}
            onchange={(e) => handleCheckbox(opt.value, e.target.checked)}
            class="accent-amber rounded"
          />
          {opt.label}
        </label>
      {/each}
    </div>
  {/if}
  </label>
</div>
