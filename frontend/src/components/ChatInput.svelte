<script>
  let { onSend, disabled = false, activeQuestion = null, onFocus: onFocusCb = null } = $props()
  let inputText = $state('')
  let inputEl
  let highlightedIndex = $state(-1)
  let dropdownOpen = $state(false)

  const options = $derived(activeQuestion?.options ?? null)
  const optionLabels = $derived(activeQuestion?.option_labels ?? null)
  const isMultiSelect = $derived(activeQuestion?.multi_select ?? false)
  const defaultValue = $derived(activeQuestion?.default_value ?? null)
  const useChips = $derived(options && options.length < 5)
  const useAutocomplete = $derived(options && options.length >= 5)

  // Pair each option value with its display label
  const optionItems = $derived(
    options?.map((v, i) => ({ value: v, label: optionLabels?.[i] ?? v })) ?? null
  )

  // The active search segment (accounts for multi-select commas)
  const currentQuery = $derived.by(() => {
    if (!useAutocomplete) return ''
    const raw = inputText
    if (isMultiSelect) {
      const parts = raw.split(',')
      return parts[parts.length - 1].trim()
    }
    return raw.trim()
  })

  const filteredItems = $derived.by(() => {
    if (!useAutocomplete || !optionItems) return []
    if (!currentQuery) return optionItems
    const q = currentQuery.toLowerCase()
    return optionItems.filter(item => item.label.toLowerCase().includes(q))
  })

  // Ghost text: find the first option whose label starts with the current segment
  const ghostText = $derived.by(() => {
    const raw = inputText
    let currentSegment = raw
    let prefix = ''

    if (isMultiSelect) {
      const parts = raw.split(',')
      currentSegment = parts[parts.length - 1].trimStart()
      if (parts.length > 1) prefix = parts.slice(0, -1).join(',') + ', '
    }

    // Empty input with no multi-select prefix: show defaultValue
    if (!currentSegment && !prefix) return defaultValue ?? ''

    if (!optionItems || !currentSegment) return ''

    const seg = currentSegment.toLowerCase()
    const match = optionItems.find(item => item.label.toLowerCase().startsWith(seg))
    if (!match) return ''

    return prefix + match.label
  })

  const ghostSuffix = $derived(
    ghostText && inputText
      ? (ghostText.toLowerCase().startsWith(inputText.toLowerCase())
          ? ghostText.slice(inputText.length)
          : '')
      : ghostText && !inputText.trim()
        ? ghostText
        : ''
  )

  const placeholderText = $derived(
    defaultValue
      ? ''
      : useAutocomplete
        ? 'Type to filter options...'
        : 'Type a message...'
  )

  // Virtualized dropdown
  const ITEM_HEIGHT = 36
  const MAX_VISIBLE = 7
  let dropdownEl = $state(null)
  let dropdownScrollTop = $state(0)

  const visibleRange = $derived.by(() => {
    const start = Math.max(0, Math.floor(dropdownScrollTop / ITEM_HEIGHT) - 2)
    const end = Math.min(filteredItems.length, start + MAX_VISIBLE + 4)
    return { start, end }
  })

  // Scroll highlighted item into view
  $effect(() => {
    if (highlightedIndex >= 0 && dropdownEl) {
      const itemTop = highlightedIndex * ITEM_HEIGHT
      const itemBottom = itemTop + ITEM_HEIGHT
      if (itemTop < dropdownEl.scrollTop) {
        dropdownEl.scrollTop = itemTop
      } else if (itemBottom > dropdownEl.scrollTop + dropdownEl.clientHeight) {
        dropdownEl.scrollTop = itemBottom - dropdownEl.clientHeight
      }
    }
  })

  function highlightLabel(label, query) {
    if (!query) return [{ text: label, match: false }]
    const lower = label.toLowerCase()
    const idx = lower.indexOf(query.toLowerCase())
    if (idx === -1) return [{ text: label, match: false }]
    return [
      { text: label.slice(0, idx), match: false },
      { text: label.slice(idx, idx + query.length), match: true },
      { text: label.slice(idx + query.length), match: false },
    ].filter(s => s.text)
  }

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
      if (dropdownOpen && filteredItems.length > 0) {
        e.preventDefault()
        const idx = highlightedIndex >= 0 ? highlightedIndex : 0
        const selected = filteredItems[idx].value
        if (isMultiSelect) {
          const parts = inputText.split(',').map(s => s.trim()).filter(Boolean)
          parts.pop()
          parts.push(selected)
          inputText = parts.join(', ') + ', '
        } else {
          inputText = selected
        }
        dropdownOpen = false
        highlightedIndex = -1
        return
      }
      if (ghostSuffix) {
        e.preventDefault()
        inputText = isMultiSelect ? ghostText + ', ' : ghostText
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
    if (dropdownOpen && filteredItems.length > 0) {
      if (e.key === 'ArrowDown') {
        e.preventDefault()
        highlightedIndex = (highlightedIndex + 1) % filteredItems.length
        return
      }
      if (e.key === 'ArrowUp') {
        e.preventDefault()
        highlightedIndex = highlightedIndex <= 0
          ? filteredItems.length - 1
          : highlightedIndex - 1
        return
      }
    }

    // Number key shortcuts for chips
    if (useChips && optionItems && !inputText.trim()) {
      const num = parseInt(e.key)
      if (num >= 1 && num <= optionItems.length) {
        e.preventDefault()
        selectChip(optionItems[num - 1].value)
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
    onFocusCb?.()
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
  {#if useChips && optionItems}
    <div class="px-4 pt-3 pb-1 flex flex-wrap gap-2">
      {#each optionItems as item, i}
        <button
          type="button"
          {disabled}
          onclick={() => selectChip(item.value)}
          class="inline-flex items-center gap-1.5 bg-canvas border border-ink/10 rounded-xl px-3 py-1.5 text-sm text-ink transition hover:bg-amber-soft hover:border-amber/40 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
        >
          <kbd class="inline-flex items-center justify-center w-5 h-5 rounded bg-ink/5 text-xs font-mono text-ink-secondary">{i + 1}</kbd>
          {item.label}
        </button>
      {/each}
    </div>
  {/if}

  <form onsubmit={handleSubmit} class="p-4 flex gap-3 relative">
    {#if dropdownOpen && filteredItems.length > 0}
      <div
        bind:this={dropdownEl}
        onscroll={() => dropdownScrollTop = dropdownEl.scrollTop}
        role="listbox"
        id="autocomplete-listbox"
        class="absolute bottom-full left-4 right-20 mb-1 bg-surface border border-ink/10 rounded-xl shadow-lg overflow-y-auto overflow-x-hidden z-10"
        style="max-height: {MAX_VISIBLE * ITEM_HEIGHT}px;"
      >
        <div style="height: {filteredItems.length * ITEM_HEIGHT}px; position: relative;">
          {#each filteredItems.slice(visibleRange.start, visibleRange.end) as item, i}
            {@const idx = visibleRange.start + i}
            <button
              type="button"
              id="autocomplete-option-{idx}"
              role="option"
              aria-selected={idx === highlightedIndex}
              onmousedown={() => selectAutocompleteOption(item.value)}
              class="absolute w-full text-left px-4 text-sm transition flex items-center {idx === highlightedIndex ? 'bg-amber-soft text-ink' : 'text-ink-secondary hover:bg-canvas'}"
              style="top: {idx * ITEM_HEIGHT}px; height: {ITEM_HEIGHT}px;"
            >
              {#each highlightLabel(item.label, currentQuery) as seg}
                <span class={seg.match ? 'text-amber font-medium' : ''}>{seg.text}</span>
              {/each}
            </button>
          {/each}
        </div>
      </div>
    {/if}

    <div class="flex-1 relative">
      {#if ghostSuffix}
        <div
          aria-hidden="true"
          class="absolute inset-0 flex items-center px-4 py-2.5 pointer-events-none overflow-hidden whitespace-nowrap text-base"
        >
          <span class="invisible">{inputText}</span><span class="text-ink-muted">{ghostSuffix}</span>
        </div>
      {/if}
      <input
        bind:this={inputEl}
        bind:value={inputText}
        type="text"
        placeholder={ghostSuffix ? '' : placeholderText}
        autocomplete="off"
        role={useAutocomplete ? 'combobox' : undefined}
        aria-expanded={useAutocomplete ? dropdownOpen && filteredItems.length > 0 : undefined}
        aria-controls={useAutocomplete ? 'autocomplete-listbox' : undefined}
        aria-activedescendant={highlightedIndex >= 0 ? `autocomplete-option-${highlightedIndex}` : undefined}
        {disabled}
        onkeydown={handleKeydown}
        oninput={handleInput}
        onfocus={handleFocus}
        onblur={handleBlur}
        class="w-full border border-ink/10 rounded-xl px-4 py-2.5 text-base text-ink placeholder:text-ink-muted focus:outline-none focus:ring-2 focus:ring-amber/25 focus:border-amber/40 transition {ghostSuffix ? 'bg-transparent' : 'bg-canvas'}"
      />
    </div>
    <button
      type="submit"
      {disabled}
      class="bg-amber text-white px-5 py-2.5 rounded-xl font-medium hover:bg-amber-hover active:scale-[0.98] transition disabled:opacity-40 cursor-pointer disabled:cursor-not-allowed"
    >
      Send
    </button>
  </form>
</div>
