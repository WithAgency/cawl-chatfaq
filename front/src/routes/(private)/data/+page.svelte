<script lang="ts">
    import ResourceView from "$lib/components/ResourceView.svelte";
    import { lang, translate } from "$lib/i18n";

    let itemsKnowledgeBase = $state<string | null>(null);
    let tab = $state("knowledge-base");

    const nameFilter = [{ type: "search" as const, placeholder: "Name", field: "search" }];
</script>

<h1>{translate($lang, "data")}</h1>
<div role="tablist">
    <button type="button" role="tab" aria-selected={tab === "knowledge-base"} onclick={() => (tab = "knowledge-base")}>
        {translate($lang, "knowledgebase")}
    </button>
    <button type="button" role="tab" aria-selected={tab === "knowledge-item"} onclick={() => (tab = "knowledge-item")}>
        {translate($lang, "knowledgeitem")}
    </button>
</div>

{#if tab === "knowledge-base"}
    <ResourceView
        readableName={translate($lang, "knowledgebase")}
        apiUrl="/back/api/language-model/knowledge-bases/"
        cardProps={{ lang: translate($lang, "lang") }}
        filters={nameFilter}
        itemActionLabel={translate($lang, "viewknowledgeitems")}
        itemActionTestId={(item) => `view knowledge items ${item.name}`}
        onItemAction={(item) => {
            itemsKnowledgeBase = String(item.id);
            tab = "knowledge-item";
        }}
    />
{:else}
    <ResourceView
        readableName={translate($lang, "knowledgeitem")}
        apiUrl="/back/api/language-model/knowledge-items/"
        columns={[{ key: "title", label: translate($lang, "title") }]}
        filters={nameFilter}
        query={itemsKnowledgeBase ? { knowledge_base__id: itemsKnowledgeBase } : {}}
    />
{/if}
