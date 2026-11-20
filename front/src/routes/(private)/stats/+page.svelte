<script lang="ts">
    import { onMount } from "svelte";
    import { lang, translate } from "$lib/i18n";

    let total = $state<number | null>(null);

    onMount(async () => {
        const response = await fetch("/back/api/broker/stats/");
        if (response.ok) {
            const body = await response.json();
            total = body.total_conversations ?? 0;
        } else {
            total = 0;
        }
    });
</script>

<h1>{translate($lang, "stats")}</h1>
{#if total !== null}
    <div data-testid={`stat ${translate($lang, "totalconversations")}`}>
        <div>{translate($lang, "totalconversations")}</div>
        <div>{total}</div>
    </div>
{/if}
