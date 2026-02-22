<script>
  let { onSend, disabled = false } = $props()
  let inputText = $state('')
  let inputEl

  function handleSubmit(e) {
    e.preventDefault()
    const text = inputText.trim()
    if (!text) return
    onSend(text)
    inputText = ''
  }

  export function focus() {
    inputEl?.focus()
  }
</script>

<form onsubmit={handleSubmit} class="p-4 bg-white border-t flex gap-2">
  <input
    bind:this={inputEl}
    bind:value={inputText}
    type="text"
    placeholder="Type a message..."
    autocomplete="off"
    {disabled}
    class="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
  />
  <button
    type="submit"
    {disabled}
    class="bg-blue-600 text-white px-5 py-2 rounded-lg hover:bg-blue-700 transition disabled:opacity-50"
  >
    Send
  </button>
</form>
