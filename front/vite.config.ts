import type { ClientRequest, IncomingMessage } from "node:http";
import { sveltekit } from "@sveltejs/kit/vite";
import { defineConfig, loadEnv } from "vite";
import path from "node:path";

function forwardToken(proxy: { on: (event: string, handler: (proxyReq: ClientRequest, req: IncomingMessage) => void) => void }) {
    proxy.on("proxyReq", (proxyReq, req) => {
        if (proxyReq.getHeader("authorization")) {
            return;
        }
        const raw = req.headers.cookie ?? "";
        const cookie = Array.isArray(raw) ? raw.join("; ") : raw;
        const token = /(?:^|;\s*)token=([^;]+)/.exec(cookie)?.[1];
        if (token) {
            proxyReq.setHeader("authorization", `Token ${decodeURIComponent(token)}`);
        }
    });
}

export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, process.cwd(), "");

    return {
        plugins: [sveltekit()],
        resolve: {
            alias: {
                "chatfaq-widget": path.resolve(import.meta.dirname, "../widget/src/index.ts"),
            },
        },
        server: {
            // Playwright reaches this server as http://admin:3000 inside Compose.
            allowedHosts: true,
            fs: {
                allow: [".."],
            },
            proxy: {
                // Compose injects these into the process. loadEnv only reads .env files.
                "/back": {
                    target: process.env.VITE_API_URL || env.VITE_API_URL || process.env.API_URL,
                    ws: true,
                    configure: forwardToken,
                },
                "/ray": {
                    target: process.env.VITE_RAY_URL || env.VITE_RAY_URL || "http://127.0.0.1:8265",
                    ws: true,
                },
            },
        },
        build: {
            target: "es2017",
        },
    };
});
