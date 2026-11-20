<script lang="ts">
    import { onMount, tick } from "svelte";

    let { children } = $props();

    onMount(async () => {
        // Child layouts show the menu from onMount. tick() lets that paint
        // before the scenarios treat the page as ready.
        await tick();
        const root = document.getElementById("__nuxt");
        if (root) {
            Object.assign(root, { __vue_app__: true });
        }
    });
</script>

{@render children()}
