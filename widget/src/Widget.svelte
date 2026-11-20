<script lang="ts">
    interface Message {
        id: number;
        text: string;
    }

    let {
        chatfaqApi = "",
        widgetConfigId = "",
        title = "Hello there",
        subtitle = "",
        fullScreen = false,
        onlyChat = false,
        noMenu = false,
        startWithHistoryClosed = false,
        fitToParent = false,
        customCss = "",
    } = $props();

    let opened = $state(Boolean(fullScreen || fitToParent));
    let darkMode = $state(false);
    let historyOpened = $state(!startWithHistoryClosed && !onlyChat && !noMenu);
    let messages = $state<Message[]>([]);
    let heading = $state(title);
    let subheading = $state(subtitle);
    let nextId = 1;

    function flag(value: unknown): boolean {
        return value === true || value === "true" || value === "";
    }

    $effect(() => {
        if (flag(fullScreen) || flag(fitToParent)) opened = true;
        if (flag(startWithHistoryClosed) || flag(onlyChat) || flag(noMenu)) historyOpened = false;
        if (customCss) {
            let style = document.getElementById("chatfaq-custom-css");
            if (!style) {
                style = document.createElement("style");
                style.id = "chatfaq-custom-css";
                document.head.append(style);
            }
            style.textContent = String(customCss);
        }
    });

    $effect(() => {
        const id = widgetConfigId;
        const api = chatfaqApi || (typeof window === "undefined" ? "" : window.location.origin);
        if (!id || !api) return;
        fetch(`${api}/back/api/widget/widgets/${id}/`, { headers: { "widget-id": String(id) } })
            .then((response) => (response.ok ? response.json() : null))
            .then((body) => {
                if (!body) return;
                if (body.title) heading = body.title;
                if (body.subtitle) subheading = body.subtitle;
            })
            .catch(() => undefined);
    });

    function send(input: HTMLElement) {
        const text = input.innerText.trim();
        if (!text) return;
        messages = [...messages, { id: nextId++, text }];
        input.innerText = "";
    }
</script>

<div class="chatfaq-widget" class:dark={darkMode}>
    {#if opened}
        <div class="panel">
            {#if historyOpened}
                <aside>
                    <p>New conversation</p>
                    <button type="button" data-testid="color theme" onclick={() => (darkMode = !darkMode)}>
                        {darkMode ? "Show light mode" : "Show dark mode"}
                    </button>
                </aside>
            {/if}
            <section>
                {#if heading}<h2>{heading}</h2>{/if}
                {#if subheading}<p>{subheading}</p>{/if}
                <div class="messages">
                    {#each messages as message (message.id)}
                        <p>{message.text}</p>
                    {/each}
                </div>
                <div class="composer">
                    <div data-testid="chat prompt" class="prompt" contenteditable="true"></div>
                    <button
                        type="button"
                        data-testid="send message"
                        onclick={(event) => {
                            const prompt = event.currentTarget.parentElement?.querySelector("[data-testid='chat prompt']");
                            if (prompt instanceof HTMLElement) send(prompt);
                        }}
                    >
                        Send
                    </button>
                </div>
            </section>
        </div>
    {/if}
    {#if !flag(fullScreen) && !flag(fitToParent)}
        <button type="button" data-testid="open widget" class:opened onclick={() => (opened = !opened)}>
            {opened ? "Close" : "Open"}
        </button>
    {/if}
</div>

<style>
    .chatfaq-widget {
        font-family: "Open Sans", sans-serif;
    }
    .panel {
        display: flex;
        width: min(720px, 100%);
        min-height: 420px;
        background: white;
        border: 1px solid #ddd;
    }
    .dark .panel {
        background: #1c1b22;
        color: white;
    }
    aside {
        width: 180px;
        border-right: 1px solid #eee;
        padding: 12px;
    }
    section {
        flex: 1;
        display: flex;
        flex-direction: column;
        padding: 12px;
    }
    .messages {
        flex: 1;
    }
    .composer {
        display: flex;
        gap: 8px;
    }
    .prompt {
        flex: 1;
        min-height: 40px;
        border: 1px solid #ccc;
        padding: 8px;
    }
    button[data-testid="open widget"] {
        position: fixed;
        right: 24px;
        bottom: 24px;
    }
</style>
