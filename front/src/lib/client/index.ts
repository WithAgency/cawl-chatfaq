/**
 * Small typescript-fetch style runtime for the stable Knox endpoints.
 * `generate_ts_client` overwrites this directory from the OpenAPI schema.
 */

export interface FetchParams {
    url: string;
    init: RequestInit;
}

export interface RequestContext {
    url: string;
    init: RequestInit;
}

export interface ResponseContext {
    url: string;
    init: RequestInit;
    response: Response;
}

export interface Middleware {
    pre?(context: RequestContext): Promise<FetchParams | void>;
    post?(context: ResponseContext): Promise<Response | void>;
}

export type FetchAPI = typeof fetch;

export interface ConfigurationParameters {
    basePath?: string;
    fetchApi?: FetchAPI;
    middleware?: Middleware[];
}

export class Configuration {
    basePath: string;
    fetchApi: FetchAPI;
    middleware: Middleware[];

    constructor(params: ConfigurationParameters = {}) {
        this.basePath = params.basePath ?? "";
        this.fetchApi = params.fetchApi ?? fetch;
        this.middleware = params.middleware ?? [];
    }
}

export class ApiError extends Error {
    constructor(
        message: string,
        readonly status: number,
    ) {
        super(message);
    }
}

export interface User {
    is_authenticated?: boolean;
    first_name?: string;
    last_name?: string;
    email?: string;
}

async function request(config: Configuration, path: string, init: RequestInit): Promise<Response> {
    let url = `${config.basePath}${path}`;
    let next: RequestInit = { ...init, headers: { ...(init.headers as Record<string, string>) } };

    for (const middleware of config.middleware) {
        const patched = await middleware.pre?.({ url, init: next });
        if (patched) {
            url = patched.url ?? url;
            next = patched.init ?? next;
        }
    }

    let response = await config.fetchApi(url, next);

    for (const middleware of config.middleware) {
        const patched = await middleware.post?.({ url, init: next, response });
        if (patched) {
            response = patched;
        }
    }

    return response;
}

export class MeApi {
    constructor(private readonly config: Configuration) {}

    async getCurrentUser(): Promise<User> {
        const response = await request(this.config, "/back/api/people/people/", { method: "GET" });
        if (!response.ok) {
            throw new ApiError("Current user request failed", response.status);
        }
        return response.json();
    }
}

export class AuthApi {
    constructor(private readonly config: Configuration) {}

    async logout(): Promise<void> {
        const response = await request(this.config, "/back/api/logout/", { method: "POST" });
        if (!response.ok) {
            throw new ApiError("Logout failed", response.status);
        }
    }
}
