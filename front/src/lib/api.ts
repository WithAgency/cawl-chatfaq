import { dev } from "$app/environment";
import type { Cookies } from "@sveltejs/kit";
import {
    AuthApi,
    Configuration,
    MeApi,
    type FetchAPI,
    type FetchParams,
    type Middleware,
    type RequestContext,
    type ResponseContext,
} from "$lib/client";

export interface ApiClient {
    auth: AuthApi;
    me: MeApi;
}

export interface ApiClientOptions {
    fetch: FetchAPI;
    cookies?: Cookies;
}

class TokenMiddleware implements Middleware {
    constructor(private readonly cookies: Cookies) {}

    async pre(context: RequestContext): Promise<FetchParams | void> {
        const token = this.cookies.get("token");
        if (!token) {
            return context;
        }
        return {
            ...context,
            init: {
                ...context.init,
                headers: {
                    ...context.init.headers,
                    Authorization: `Token ${token}`,
                },
            },
        };
    }
}

class CsrfMiddleware implements Middleware {
    constructor(private readonly cookies: Cookies) {}

    async pre(context: RequestContext): Promise<FetchParams | void> {
        const cookie = this.cookies.get("csrftoken");
        if (!cookie) {
            return context;
        }
        return {
            ...context,
            init: {
                ...context.init,
                headers: {
                    ...context.init.headers,
                    "X-CSRFToken": cookie,
                },
            },
        };
    }
}

interface CookieArg {
    name: string;
    value: string;
}

function parseCookieArg(arg: string): CookieArg | undefined {
    const match = arg.match(/^([^=]+)(=(.*))?$/);
    if (!match) {
        return;
    }
    return { name: match[1], value: match[3] || "" };
}

class CookieParrotMiddleware implements Middleware {
    constructor(private readonly cookies: Cookies) {}

    async post(context: ResponseContext): Promise<Response | void> {
        context.response.headers.getSetCookie().forEach((cookie) => {
            const parts = cookie.split(";").map((part) => part.trim());
            const options: Parameters<Cookies["set"]>[2] = {
                httpOnly: false,
                secure: !dev,
                path: "/",
            };
            const core = parseCookieArg(parts[0]);
            if (!core) {
                return;
            }
            parts.slice(1).forEach((part) => {
                const parsed = parseCookieArg(part);
                if (!parsed) {
                    return;
                }
                const name = parsed.name.toLowerCase();
                if (name === "httponly") {
                    options.httpOnly = true;
                } else if (name === "max-age") {
                    const maxAge = parseInt(parsed.value, 10);
                    if (!Number.isNaN(maxAge)) {
                        options.maxAge = maxAge;
                    }
                } else if (name === "path") {
                    options.path = parsed.value;
                } else if (name === "samesite" && ["strict", "lax", "none"].includes(parsed.value.toLowerCase())) {
                    options.sameSite = parsed.value.toLowerCase() as "strict" | "lax" | "none";
                } else if (name === "secure") {
                    options.secure = true;
                } else if (name === "expires") {
                    options.expires = new Date(parsed.value);
                }
            });
            this.cookies.set(core.name, core.value, options);
        });
        return context.response;
    }
}

export default function makeApiClient(options: ApiClientOptions): ApiClient {
    const config = new Configuration({
        basePath: "http://api",
        fetchApi: options.fetch,
        middleware: options.cookies
            ? [
                  new TokenMiddleware(options.cookies),
                  new CsrfMiddleware(options.cookies),
                  new CookieParrotMiddleware(options.cookies),
              ]
            : [],
    });

    return {
        auth: new AuthApi(config),
        me: new MeApi(config),
    };
}
