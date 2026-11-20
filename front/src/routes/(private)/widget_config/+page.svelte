<script lang="ts">
    import ResourceView from "$lib/components/ResourceView.svelte";
    import { lang, translate } from "$lib/i18n";

    let tab = $state("widget");
</script>

<h1>{translate($lang, "widgetconfig")}</h1>
<div role="tablist">
    <button type="button" role="tab" aria-selected={tab === "widget"} onclick={() => (tab = "widget")}>
        {translate($lang, "widget")}
    </button>
    <button type="button" role="tab" aria-selected={tab === "theme"} onclick={() => (tab = "theme")}>
        {translate($lang, "theme")}
    </button>
</div>

{#if tab === "widget"}
    <ResourceView
        readableName={translate($lang, "widget")}
        apiUrl="/back/api/widget/widgets/"
        cardProps={{ domain: translate($lang, "domain") }}
        sections={[
            { title: translate($lang, "general"), fields: ["name", "domain"] },
        ]}
    />
{:else}
    <ResourceView
        readableName={translate($lang, "theme")}
        apiUrl="/back/api/widget/themes/"
        cardProps={{ name: translate($lang, "name") }}
        sections={[{ title: translate($lang, "general"), fields: ["name"] }]}
    />
{/if}
