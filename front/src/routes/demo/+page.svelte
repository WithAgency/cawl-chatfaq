<script lang="ts">
    import { page } from "$app/state";
    import { onMount } from "svelte";

    const widgetId = page.url.searchParams.get("widget_id") ?? "";

    onMount(async () => {
        const widget = await import("chatfaq-widget");
        if (!customElements.get("chatfaq-widget")) {
            customElements.define("chatfaq-widget", widget.ChatfaqWidgetCustomElement);
        }
        const element = document.createElement("chatfaq-widget");
        element.dataset.widgetConfigId = widgetId;
        element.dataset.chatfaqApi = window.location.origin;
        element.dataset.chatfaqWs = `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.host}`;
        element.dataset.fsmDef = "llm_fsm";
        document.getElementById("demo")?.append(element);
    });
</script>

<div id="demo"></div>
