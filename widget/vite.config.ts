import { resolve } from "node:path";
import { defineConfig } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";
import cssInjectedByJsPlugin from "vite-plugin-css-injected-by-js";

export default defineConfig({
    plugins: [svelte(), cssInjectedByJsPlugin()],
    build: {
        lib: {
            entry: resolve(import.meta.dirname, "src/index.ts"),
            name: "ChatFAQWidget",
            fileName: "chatfaq-widget",
        },
        rollupOptions: {
            external: [],
        },
    },
});
