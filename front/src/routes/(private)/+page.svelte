<script lang="ts">
    import { goto } from "$app/navigation";
    import { onMount } from "svelte";
    import { lang, translate } from "$lib/i18n";

    let { data } = $props();
    let llms = $state<Array<Record<string, unknown>>>([]);
    let widgets = $state<Array<Record<string, unknown>>>([]);
    let sdks = $state<Array<Record<string, unknown>>>([]);

    async function load() {
        const [llmResponse, widgetResponse, sdkResponse] = await Promise.all([
            fetch("/back/api/language-model/llm-configs/?limit=50&offset=0"),
            fetch("/back/api/widget/widgets/?limit=50&offset=0"),
            fetch("/back/api/broker/sdks/?limit=50&offset=0"),
        ]);
        llms = llmResponse.ok ? ((await llmResponse.json()).results ?? []) : [];
        widgets = widgetResponse.ok ? ((await widgetResponse.json()).results ?? []) : [];
        sdks = sdkResponse.ok ? ((await sdkResponse.json()).results ?? []) : [];
    }

    async function toggle(item: Record<string, unknown>) {
        const response = await fetch(`/back/api/language-model/llm-configs/${item.id}/`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ enabled: !item.enabled }),
        });
        if (response.ok) {
            const body = await response.json();
            item.enabled = body.enabled;
            llms = llms.map((llm) => (llm.id === item.id ? body : llm));
        }
    }

    onMount(load);
</script>

<h1>{translate($lang, "welcome", { name: data.user?.first_name ?? "" })}</h1>

<section>
    <h2>{translate($lang, "fsms")}</h2>
    {#if sdks.length === 0}
        <p data-testid="no sdks">{translate($lang, "nosdks")}</p>
    {/if}
</section>

<section>
    <h2>{translate($lang, "llms")}</h2>
    {#if llms.length === 0}
        <p data-testid="no llms">{translate($lang, "nollms")}</p>
    {/if}
    {#each llms as item}
        <article>
            <button type="button" data-testid={`${item.name} card`} onclick={() => goto("/ai_config")}>
                {item.name}
            </button>
            <label data-testid={`enable ${item.name}`}>
                {translate($lang, "enabled")}
                <input type="checkbox" checked={Boolean(item.enabled)} onchange={() => toggle(item)} />
            </label>
        </article>
    {/each}
</section>

<section>
    <h2>{translate($lang, "widgets")}</h2>
    {#if widgets.length === 0}
        <p data-testid="no widgets">{translate($lang, "nowidgets")}</p>
    {/if}
    {#each widgets as item}
        <button type="button" data-testid={`${item.name} card`} onclick={() => goto("/widget_config")}>
            {item.name}
        </button>
    {/each}
</section>
