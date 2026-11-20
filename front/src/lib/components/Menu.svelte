<script lang="ts">
    import { lang, translate, type Lang } from "$lib/i18n";

    let { useRay = false }: { useRay?: boolean } = $props();
    let open = $state(false);

    const options: { code: Lang; label: string }[] = [
        { code: "en", label: "Language: EN" },
        { code: "es", label: "Lengua: ES" },
        { code: "fr", label: "Langue: FR" },
    ];

    function choose(code: Lang) {
        lang.set(code);
        localStorage.setItem("chatfaq-lang", code);
        open = false;
    }
</script>

<nav class="menu">
    <a href="/">{translate($lang, "dashboard")}</a>
    <a data-testid="labeling" href="/labeling">{translate($lang, "labeling")}</a>
    <a data-testid="data" href="/data">{translate($lang, "data")}</a>
    <a data-testid="AI config" href="/ai_config">{translate($lang, "aiconfiguration")}</a>
    <a data-testid="widget config" href="/widget_config">{translate($lang, "widgetconfig")}</a>
    <a data-testid="stats" href="/stats">{translate($lang, "stats")}</a>
    <a data-testid="user management" href="/user_management">{translate($lang, "usermanagement")}</a>
    {#if useRay}
        <a data-testid="task history" href="/task_history">{translate($lang, "taskhistory")}</a>
    {/if}
    <button type="button" data-testid="language" onclick={() => (open = !open)}>
        {options.find((option) => option.code === $lang)?.label}
    </button>
    {#if open}
        {#each options as option}
            <button type="button" onclick={() => choose(option.code)}>{option.label}</button>
        {/each}
    {/if}
    <a data-testid="log out" href="/logout">{translate($lang, "logout")}</a>
</nav>
