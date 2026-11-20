<script lang="ts">
    import ResourceView from "$lib/components/ResourceView.svelte";
    import { lang, translate } from "$lib/i18n";

    let { data } = $props();
    let tab = $state("llm");
</script>

<h1>{translate($lang, "aiconfiguration")}</h1>
<div role="tablist">
    <button type="button" role="tab" aria-selected={tab === "llm"} onclick={() => (tab = "llm")}>
        {translate($lang, "llm")}
    </button>
    {#if data.useRay}
        <button type="button" role="tab" aria-selected={tab === "retriever"} onclick={() => (tab = "retriever")}>
            {translate($lang, "retriever")}
        </button>
    {/if}
    <button type="button" role="tab" aria-selected={tab === "prompt"} onclick={() => (tab = "prompt")}>
        {translate($lang, "prompt")}
    </button>
    <button type="button" role="tab" aria-selected={tab === "generation"} onclick={() => (tab = "generation")}>
        {translate($lang, "generation")}
    </button>
</div>

{#if tab === "llm"}
    <ResourceView
        readableName={translate($lang, "llm")}
        apiUrl="/back/api/language-model/llm-configs/"
        cardProps={{ llm_type: translate($lang, "llmtype"), llm_name: translate($lang, "llmname") }}
        secretFields={["api_key"]}
    />
{:else if tab === "retriever"}
    <ResourceView
        readableName={translate($lang, "retriever")}
        apiUrl="/back/api/language-model/retriever-configs/"
        cardProps={{ name: translate($lang, "name") }}
    />
    <p>{translate($lang, "reindex")}</p>
{:else if tab === "prompt"}
    <ResourceView
        readableName={translate($lang, "prompt")}
        apiUrl="/back/api/language-model/prompt-configs/"
        cardProps={{ name: translate($lang, "name") }}
    />
{:else}
    <ResourceView
        readableName={translate($lang, "generation")}
        apiUrl="/back/api/language-model/generation-configs/"
        cardProps={{ temperature: translate($lang, "temperature") }}
    />
{/if}
