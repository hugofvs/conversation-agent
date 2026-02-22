<script>
  let { onSend, disabled = false, activeQuestion = null } = $props()
  let inputText = $state('')
  let inputEl
  let highlightedIndex = $state(-1)
  let dropdownOpen = $state(false)

  const options = $derived(activeQuestion?.options ?? null)
  const isMultiSelect = $derived(activeQuestion?.multi_select ?? false)
  const defaultValue = $derived(activeQuestion?.default_value ?? null)
  const useChips = $derived(options && options.length < 5)
  const useAutocomplete = $derived(options && options.length >= 5)

  const filteredOptions = $derived.by(() => {
    if (!useAutocomplete || !options) return []
    const raw = inputText
    let query = raw
    if (isMultiSelect) {
      const parts = raw.split(',')
      query = parts[parts.length - 1].trim()
    }
    if (!query) return options
    const q = query.toLowerCase()
    return options.filter(o => o.toLowerCase().includes(q))
  })

  const placeholderText = $derived(
    defaultValue
      ? `${defaultValue} (press Tab)`
      : useAutocomplete
        ? 'Type to filter options...'
        : 'Type a message...'
  )

  function send(text) {
    const val = text.trim()
    if (!val) return
    onSend(val)
    inputText = ''
    dropdownOpen = false
    highlightedIndex = -1
  }

  function handleSubmit(e) {
    e.preventDefault()
    send(inputText)
  }

  function selectChip(value) {
    send(value)
  }

  function selectAutocompleteOption(option) {
    if (isMultiSelect) {
      const parts = inputText.split(',').map(s => s.trim()).filter(Boolean)
      // replace the in-progress segment with the selected option
      parts.pop()
      parts.push(option)
      inputText = parts.join(', ') + ', '
      highlightedIndex = -1
      inputEl?.focus()
    } else {
      send(option)
    }
  }

  function handleKeydown(e) {
    // Tab: fill default value or select autocomplete option
    if (e.key === 'Tab') {
      if (dropdownOpen && filteredOptions.length > 0) {
        e.preventDefault()
        const idx = highlightedIndex >= 0 ? highlightedIndex : 0
        selectAutocompleteOption(filteredOptions[idx])
        return
      }
      if (defaultValue && !inputText.trim()) {
        e.preventDefault()
        inputText = defaultValue
        return
      }
    }

    // Escape: close dropdown
    if (e.key === 'Escape' && dropdownOpen) {
      e.preventDefault()
      dropdownOpen = false
      highlightedIndex = -1
      return
    }

    // Arrow navigation in autocomplete
    if (dropdownOpen && filteredOptions.length > 0) {
      if (e.key === 'ArrowDown') {
        e.preventDefault()
        highlightedIndex = (highlightedIndex + 1) % filteredOptions.length
        return
      }
      if (e.key === 'ArrowUp') {
        e.preventDefault()
        highlightedIndex = highlightedIndex <= 0
          ? filteredOptions.length - 1
          : highlightedIndex - 1
        return
      }
    }

    // Number key shortcuts for chips
    if (useChips && !inputText.trim()) {
      const num = parseInt(e.key)
      if (num >= 1 && num <= options.length) {
        e.preventDefault()
        selectChip(options[num - 1])
        return
      }
    }
  }

  function handleInput() {
    if (useAutocomplete) {
      dropdownOpen = true
      highlightedIndex = -1
    }
  }

  function handleFocus() {
    if (useAutocomplete) {
      dropdownOpen = true
    }
  }

  function handleBlur(e) {
    // Delay closing so click on dropdown option can fire
    setTimeout(() => { dropdownOpen = false }, 150)
  }

  export function focus() {
    inputEl?.focus()
  }
</script>

<div class="bg-surface border-t border-ink/8">
  {#if useChips && options}
    <div class="px-4 pt-3 pb-1 flex flex-wrap gap-2">
      {#each options as option, i}
        <button
          type="button"
          {disabled}
          onclick={() => selectChip(option)}
          class="inline-flex items-center gap-1.5 bg-canvas border border-ink/10 rounded-xl px-3 py-1.5 text-sm text-ink transition hover:bg-amber-soft hover:border-amber/40 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
        >
          <kbd class="inline-flex items-center justify-center w-5 h-5 rounded bg-ink/5 text-xs font-mono text-ink-secondary">{i + 1}</kbd>
          {option}
        </button>
      {/each}
    </div>
  {/if}

  <form onsubmit={handleSubmit} class="p-4 flex gap-3 relative">
    {#if dropdownOpen && filteredOptions.length > 0}
      <div class="absolute bottom-full left-4 right-20 mb-1 bg-surface border border-ink/10 rounded-xl shadow-lg max-h-48 overflow-y-auto z-10">
        {#each filteredOptions as option, i}
          <button
            type="button"
            onmousedown={() => selectAutocompleteOption(option)}
            class="w-full text-left px-4 py-2 text-sm transition {i === highlightedIndex ? 'bg-amber-soft text-ink' : 'text-ink-secondary hover:bg-canvas'}"
          >
            {option}
          </button>
        {/each}
      </div>
    {/if}

    <input
      bind:this={inputEl}
      bind:value={inputText}
      type="text"
      placeholder={placeholderText}
      autocomplete="off"
      {disabled}
      onkeydown={handleKeydown}
      oninput={handleInput}
      onfocus={handleFocus}
      onblur={handleBlur}
      class="flex-1 bg-canvas border border-ink/10 rounded-xl px-4 py-2.5 text-ink placeholder:text-ink-muted focus:outline-none focus:ring-2 focus:ring-amber/25 focus:border-amber/40 transition"
    />
    <button
      type="submit"
      {disabled}
      class="bg-amber text-white px-5 py-2.5 rounded-xl font-medium hover:bg-amber-hover active:scale-[0.98] transition disabled:opacity-40 cursor-pointer disabled:cursor-not-allowed"
    >
      Send
    </button>
  </form>
</div>
