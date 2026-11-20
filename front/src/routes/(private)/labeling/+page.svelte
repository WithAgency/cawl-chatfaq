<script lang="ts">
    import ResourceView from "$lib/components/ResourceView.svelte";
    import { lang, translate } from "$lib/i18n";

    let selected = $state<{ name?: string } | null>(null);
</script>

<h1>{translate($lang, "labeling")}</h1>

{#if selected}
    <button type="button" data-testid="back" onclick={() => (selected = null)}>{translate($lang, "back")}</button>
    <p>{selected.name}</p>
{:else}
    <ResourceView
        readableName={translate($lang, "conversation")}
        apiUrl="/back/api/broker/conversations/"
        readOnly={true}
        columns={[
            { key: "name", label: translate($lang, "name") },
            { key: "user_id", label: translate($lang, "userid") },
        ]}
        filters={[
            { type: "search", placeholder: "Name", field: "search" },
            { type: "bool", placeholder: translate($lang, "withuserfeedback"), field: "user_feedback_exists" },
            { type: "bool", placeholder: translate($lang, "reviewed"), field: "reviewed" },
        ]}
        onOpen={(item) => (selected = item)}
    />
{/if}
