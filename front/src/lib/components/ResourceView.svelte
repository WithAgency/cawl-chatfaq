<script lang="ts">
    import { onMount } from "svelte";
    import { countLabel, lang, translate } from "$lib/i18n";

    interface FilterSpec {
        type: "search" | "bool";
        placeholder: string;
        field: string;
    }

    interface Section {
        title: string;
        fields: string[];
    }

    interface Column {
        key: string;
        label: string;
    }

    interface SchemaProp {
        type?: string;
        readOnly?: boolean;
        title?: string;
    }

    interface Item {
        id?: string;
        name?: string;
        [key: string]: unknown;
    }

    let {
        readableName,
        apiUrl,
        titleProps = ["name"],
        cardProps = {},
        columns = [],
        filters = [],
        sections = null,
        excludeFields = [],
        secretFields = ["password", "api_key"],
        readOnly = false,
        query = {},
        itemActionTestId = null,
        itemActionLabel = "",
        onItemAction = (_item: Item) => {},
        onOpen = null,
    }: {
        readableName: string;
        apiUrl: string;
        titleProps?: string[];
        cardProps?: Record<string, string>;
        columns?: Column[];
        filters?: FilterSpec[];
        sections?: Section[] | null;
        excludeFields?: string[];
        secretFields?: string[];
        readOnly?: boolean;
        query?: Record<string, string>;
        itemActionTestId?: ((item: Item) => string) | null;
        itemActionLabel?: string;
        onItemAction?: (item: Item) => void;
        onOpen?: ((item: Item) => void) | null;
    } = $props();

    let items = $state<Item[]>([]);
    let mode = $state<"list" | "write">("list");
    let editingId = $state<string | null>(null);
    let form = $state<Record<string, string>>({});
    let properties = $state<Record<string, SchemaProp>>({});
    let searchValues = $state<Record<string, string>>({});
    let saveError = $state("");
    let searchTimer: ReturnType<typeof setTimeout> | undefined;

    const useCards = $derived(Object.keys(cardProps).length > 0);
    const countText = $derived(countLabel($lang, items.length, readableName));

    function titleOf(item: Item): string {
        return titleProps
            .map((key) => item[key])
            .filter((value) => value !== undefined && value !== null && value !== "")
            .join(" ");
    }

    function names(): string[] {
        if (sections) {
            return sections.flatMap((section) => section.fields);
        }
        const fromSchema = Object.entries(properties)
            .filter(([name, prop]) => !prop.readOnly && !excludeFields.includes(name) && name !== "id")
            .map(([name]) => name);
        return fromSchema.length ? fromSchema : ["name"];
    }

    async function loadList() {
        const params = new URLSearchParams({ limit: "50", offset: "0" });
        for (const [key, value] of Object.entries(query)) {
            if (value) params.set(key, value);
        }
        for (const filter of filters) {
            const value = searchValues[filter.field];
            if (value) params.set(filter.field, value);
        }
        const response = await fetch(`${apiUrl}?${params}`);
        if (!response.ok) {
            items = [];
            return;
        }
        const body = await response.json();
        items = Array.isArray(body) ? body : (body.results ?? []);
    }

    async function loadSchema() {
        const response = await fetch("/back/api/schema/?format=json");
        if (!response.ok) return;
        const openapi = await response.json();
        const normalize = (value: string) => value.replace(/\/$/, "").replace(/^\/back/, "");
        const wanted = normalize(apiUrl);
        const path = Object.keys(openapi.paths ?? {}).find((key) => normalize(key) === wanted);
        const ref = path
            ? openapi.paths[path]?.post?.requestBody?.content?.["application/json"]?.schema?.$ref
            : undefined;
        const schemaName = ref?.split("/").pop();
        properties = schemaName ? (openapi.components?.schemas?.[schemaName]?.properties ?? {}) : {};
    }

    function startAdd() {
        editingId = null;
        form = {};
        saveError = "";
        mode = "write";
    }

    async function startEdit(item: Item) {
        if (onOpen) {
            onOpen(item);
            return;
        }
        editingId = String(item.id);
        const response = await fetch(`${apiUrl}${item.id}/`);
        const body = response.ok ? await response.json() : item;
        const next: Record<string, string> = {};
        for (const name of names()) {
            const value = body[name];
            next[name] = value === undefined || value === null ? "" : String(value);
        }
        form = next;
        saveError = "";
        mode = "write";
    }

    async function save() {
        const payload: Record<string, unknown> = {};
        for (const name of names()) {
            const value = form[name];
            if (value === undefined || value === "") continue;
            const type = properties[name]?.type;
            if (type === "integer" || type === "number") {
                payload[name] = Number(value);
            } else if (type === "boolean") {
                payload[name] = value === "true";
            } else {
                payload[name] = value;
            }
        }
        const response = await fetch(editingId ? `${apiUrl}${editingId}/` : apiUrl, {
            method: editingId ? "PUT" : "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        if (!response.ok) {
            saveError = translate($lang, "errorsavingitem");
            return;
        }
        mode = "list";
        await loadList();
    }

    function onSearch(field: string, value: string) {
        searchValues = { ...searchValues, [field]: value };
        clearTimeout(searchTimer);
        searchTimer = setTimeout(() => {
            loadList();
        }, 250);
    }

    function inputType(name: string): string {
        if (secretFields.includes(name)) return "password";
        const type = properties[name]?.type;
        if (type === "integer" || type === "number") return "number";
        return "text";
    }

    function isLong(name: string): boolean {
        return ["prompt", "content", "metadata"].includes(name);
    }

    onMount(() => {
        loadSchema();
        loadList();
    });
</script>

<div class="resource">
    {#if filters.length}
        <div class="filters">
            {#each filters as filter}
                <div data-testid={`filter ${filter.placeholder}`}>
                    {#if filter.type === "search"}
                        <input
                            data-testid={`search ${filter.placeholder}`}
                            placeholder={filter.placeholder}
                            value={searchValues[filter.field] ?? ""}
                            oninput={(event) => onSearch(filter.field, event.currentTarget.value)}
                        />
                    {:else}
                        <label>
                            <input
                                type="checkbox"
                                checked={searchValues[filter.field] === "true"}
                                onchange={(event) =>
                                    onSearch(filter.field, event.currentTarget.checked ? "true" : "")}
                            />
                            {filter.placeholder}
                        </label>
                    {/if}
                </div>
            {/each}
        </div>
    {/if}

    {#if mode === "list"}
        <div class="section-header">
            <div class="item-count">{countText}</div>
            {#if !readOnly}
                <button type="button" data-testid={`add ${readableName}`} onclick={startAdd}>
                    + {translate($lang, "additem", { readablename: readableName })}
                </button>
            {/if}
        </div>

        {#if useCards}
            <div class="cards">
                {#each items as item}
                    <article data-testid={`${titleOf(item)} card`}>
                        <button type="button" class="card-body" onclick={() => startEdit(item)}>
                            <h3>{titleOf(item)}</h3>
                            {#each Object.entries(cardProps) as [key, label]}
                                <p><span>{label}:</span> {item[key] ?? ""}</p>
                            {/each}
                        </button>
                        {#if !readOnly}
                            <button type="button" data-testid={`edit ${titleOf(item)}`} onclick={() => startEdit(item)}>
                                {translate($lang, "edit")}
                            </button>
                        {/if}
                        {#if itemActionTestId}
                            <button type="button" data-testid={itemActionTestId(item)} onclick={() => onItemAction(item)}>
                                {itemActionLabel}
                            </button>
                        {/if}
                    </article>
                {/each}
            </div>
        {:else}
            <table>
                <tbody>
                    {#each items as item}
                        <tr>
                            {#each columns as column}
                                <td>{item[column.key] ?? ""}</td>
                            {:else}
                                <td>{titleOf(item)}</td>
                            {/each}
                            {#if onOpen}
                                <td>
                                    <button type="button" data-testid={`view ${item.name ?? ""}`} onclick={() => onOpen?.(item)}>
                                        {translate($lang, "view")}
                                    </button>
                                </td>
                            {:else if !readOnly}
                                <td>
                                    <button type="button" data-testid={`edit ${titleOf(item)}`} onclick={() => startEdit(item)}>
                                        {translate($lang, "edit")}
                                    </button>
                                </td>
                            {/if}
                        </tr>
                    {/each}
                </tbody>
            </table>
        {/if}
    {:else}
        <button type="button" data-testid="back" onclick={() => (mode = "list")}>{translate($lang, "back")}</button>
        <form
            onsubmit={(event) => {
                event.preventDefault();
                save();
            }}
        >
            {#if sections}
                {#each sections as section}
                    <h2>{section.title}</h2>
                    {#each section.fields as name}
                        <label>
                            {translate($lang, name)}
                            {#if isLong(name)}
                                <textarea data-testid={name} bind:value={form[name]}></textarea>
                            {:else}
                                <input data-testid={name} type={inputType(name)} bind:value={form[name]} />
                            {/if}
                        </label>
                    {/each}
                {/each}
            {:else}
                {#each names() as name}
                    <label>
                        {translate($lang, name)}
                        {#if isLong(name)}
                            <textarea data-testid={name} bind:value={form[name]}></textarea>
                        {:else}
                            <input data-testid={name} type={inputType(name)} bind:value={form[name]} />
                        {/if}
                    </label>
                {/each}
            {/if}
            {#if saveError}<p>{saveError}</p>{/if}
            <button type="submit" data-testid="save changes">{translate($lang, "saved")}</button>
        </form>
    {/if}
</div>
