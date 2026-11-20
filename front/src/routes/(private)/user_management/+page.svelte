<script lang="ts">
    import ResourceView from "$lib/components/ResourceView.svelte";
    import { lang, translate } from "$lib/i18n";

    let tab = $state("user");
</script>

<h1>{translate($lang, "usermanagement")}</h1>
<div role="tablist">
    <button type="button" role="tab" aria-selected={tab === "user"} onclick={() => (tab = "user")}>
        {translate($lang, "user")}
    </button>
    <button type="button" role="tab" aria-selected={tab === "group"} onclick={() => (tab = "group")}>
        {translate($lang, "grouppermissions")}
    </button>
</div>

{#if tab === "user"}
    <ResourceView
        readableName={translate($lang, "user")}
        apiUrl="/back/api/people/users/"
        titleProps={["first_name", "last_name"]}
        cardProps={{ email: translate($lang, "email") }}
        sections={[
            {
                title: translate($lang, "userinformation"),
                fields: ["first_name", "last_name", "email", "password"],
            },
            {
                title: translate($lang, "userpermissions"),
                fields: ["is_active", "is_staff", "is_superuser"],
            },
        ]}
        secretFields={["password"]}
    />
{:else}
    <ResourceView
        readableName={translate($lang, "group")}
        apiUrl="/back/api/people/groups/"
        cardProps={{ name: translate($lang, "name") }}
        sections={[{ title: translate($lang, "general"), fields: ["name"] }]}
    />
{/if}
