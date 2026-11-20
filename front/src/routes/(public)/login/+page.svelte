<script lang="ts">
    import en from "$lib/locales/en.json";

    let { form } = $props();
</script>

<main class="login">
    <h1>{en.welcometochatfaq}</h1>
    <p>{en.pleaseenteryourdetails}</p>
    <form method="POST">
        <label>
            {en.email}
            <input data-testid="email" name="email" type="email" autocomplete="username" />
        </label>
        <label>
            {en.password}
            <input data-testid="password" name="password" type="password" autocomplete="current-password" />
        </label>
        {#if form?.error}
            <p>{form.error}</p>
        {/if}
        <button data-testid="login" type="submit">{en.login}</button>
    </form>
</main>
