<script>
  let { sources = [] } = $props()
</script>

{#if sources.length > 0}
  <div class="mt-1 flex justify-start">
    <div class="text-xs text-gray-400 max-w-[75%]">
      {#each sources as source}
        <span class="inline-block mr-2">[ {source.title} ]</span>
      {/each}
    </div>
  </div>
{/if}
