<script>
  let { role, text, isError = false } = $props()

  let wrapperClass = $derived(
    role === 'user' ? 'flex justify-end' : 'flex justify-start'
  )

  let bubbleClass = $derived(
    role === 'user'
      ? 'bg-blue-600 text-white rounded-2xl rounded-br-sm px-4 py-2 max-w-[75%]'
      : `bg-white text-gray-800 rounded-2xl rounded-bl-sm px-4 py-2 max-w-[75%] shadow${isError ? ' text-red-600' : ''}`
  )
</script>

<div class={wrapperClass}>
  <div class={bubbleClass}>{text}</div>
</div>
