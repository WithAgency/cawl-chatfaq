import { env } from "$env/dynamic/private";
import type { Handle, HandleFetch } from "@sveltejs/kit";
import { sequence } from "@sveltejs/kit/hooks";
import { createAuthStateGetter } from "$lib/auth.server";

const INTERNAL_API_ORIGIN = "http://api";

interface RequestPatch {
    url?: string | URL;
    appendHeaders?: Headers;
    mode?: RequestMode;
}

async function patchRequest(request: Request, patch: RequestPatch): Promise<Request> {
    const headers = new Headers(request.headers);
    patch.appendHeaders?.forEach((value, key) => {
        headers.append(key, value);
    });
    const url = patch.url !== undefined ? patch.url : request.url;
    const mode = patch.mode !== undefined ? patch.mode : request.mode;
    const body = request.method !== "GET" && request.method !== "HEAD" ? await request.arrayBuffer() : undefined;
    return new Request(url, {
        method: request.method,
        headers,
        body,
        mode,
        redirect: request.redirect,
    });
}

function apiOrigin(): string {
    return new URL(env.API_URL || "http://127.0.0.1:8000").origin;
}

/**
 * The browser stays on this origin. /back is Django, whether the ingress
 * splits it or this process is the only server (local node, pytest).
 */
const proxyApi: Handle = async ({ event, resolve }) => {
    const { pathname, search } = event.url;
    if (pathname === "/favicon.ico") {
        return new Response(null, { status: 204 });
    }
    if (!pathname.startsWith("/back") && !pathname.startsWith("/ray")) {
        return resolve(event);
    }

    if (pathname.startsWith("/ray")) {
        const token = event.cookies.get("token");
        if (!token) {
            return new Response("Not found", { status: 404 });
        }
        const check = await fetch(`${apiOrigin()}/back/api/people/people/`, {
            headers: { Authorization: `Token ${token}` },
        });
        if (!check.ok) {
            return new Response("Not found", { status: 404 });
        }
        const ray = new URL(env.RAY_URL || "http://127.0.0.1:8265");
        const target = new URL(`${pathname.replace(/^\/ray/, "") || "/"}${search}`, ray);
        return forward(event.request, target);
    }

    const target = new URL(`${pathname}${search}`, apiOrigin());
    return forward(event.request, target, event.cookies.get("token"));
};

async function forward(request: Request, target: URL, token?: string): Promise<Response> {
    const headers = new Headers(request.headers);
    headers.delete("host");
    headers.set("host", target.host);
    if (token && !headers.has("authorization")) {
        headers.set("Authorization", `Token ${token}`);
    }
    const body =
        request.method === "GET" || request.method === "HEAD" ? undefined : await request.arrayBuffer();
    const response = await fetch(target, {
        method: request.method,
        headers,
        body,
        redirect: "follow",
    });
    const outgoing = new Headers(response.headers);
    outgoing.delete("content-encoding");
    outgoing.delete("content-length");
    return new Response(response.body, { status: response.status, headers: outgoing });
}

const authentication: Handle = async ({ event, resolve }) => {
    event.locals.getAuthState = createAuthStateGetter(event);
    return resolve(event);
};

/**
 * Server-side fetches use the sentinel origin http://api. This hook rewrites
 * it to API_URL and forwards the browser cookie. It does not run in the browser.
 */
export const handleFetch: HandleFetch = async ({ event, request, fetch }) => {
    const url = new URL(request.url, INTERNAL_API_ORIGIN);
    if (url.origin !== INTERNAL_API_ORIGIN) {
        return fetch(request);
    }
    const extraHeaders = new Headers();
    const cookie = event.request.headers.get("cookie");
    if (cookie) {
        extraHeaders.append("Cookie", cookie);
    }
    const api = apiOrigin();
    request = await patchRequest(request, {
        url: `${api}${url.pathname}${url.search}`,
        appendHeaders: extraHeaders,
        mode: "cors",
    });
    return fetch(request);
};

export const handle = sequence(proxyApi, authentication);
