<script lang="ts">
    import { onMount } from "svelte";
    import Menu from "$lib/components/Menu.svelte";
    import { lang } from "$lib/i18n";
    import "../../app.css";

    let { data, children } = $props();
    let ready = $state(false);

    onMount(() => {
        const stored = localStorage.getItem("chatfaq-lang");
        if (stored === "en" || stored === "es" || stored === "fr") {
            lang.set(stored);
        }
        // Login lands on this page and clicks the menu at once. The button
        // stays out of the HTML until its handler exists.
        ready = true;
    });
</script>

<div class="shell">
    {#if ready}
        <Menu useRay={data.useRay} />
    {/if}
    <main>
        {@render children()}
    </main>
</div>
