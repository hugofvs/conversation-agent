<script>
  let { role, text, isError = false } = $props()
</script>

{#if role === 'user'}
  <div class="flex justify-end">
    <div class="bg-amber text-white rounded-2xl rounded-br-sm px-5 py-3 max-w-[75%] text-[15px] leading-relaxed">
      {text}
    </div>
  </div>
{:else}
  <div class="flex justify-start">
    <div
      class="bg-surface rounded-2xl rounded-bl-sm px-5 py-3 max-w-[75%] text-[15px] leading-relaxed shadow-[0_1px_4px_rgba(44,37,32,0.06)]"
      class:text-red-700={isError}
    >
      {text}
    </div>
  </div>
{/if}
