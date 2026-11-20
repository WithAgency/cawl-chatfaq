import adapter from "@sveltejs/adapter-node";
import { vitePreprocess } from "@sveltejs/vite-plugin-svelte";

/** @type {import('@sveltejs/kit').Config} */
const config = {
    preprocess: vitePreprocess(),
    kit: {
        adapter: adapter(),
        // Django remains the authority for CSRF. The browser only talks to this origin.
        csrf: {
            trustedOrigins: ["*"],
        },
    },
};

export default config;
