<script>
  let { sources = [] } = $props()
</script>

{#if sources.length > 0}
  <div class="mt-1.5 flex justify-start">
    <div class="max-w-[75%] flex flex-wrap gap-1.5">
      {#each sources as source}
        <span class="inline-block text-xs text-ink-tertiary bg-canvas border border-ink/6 px-2 py-0.5 rounded-md">
          {source.title}
        </span>
      {/each}
    </div>
  </div>
{/if}
