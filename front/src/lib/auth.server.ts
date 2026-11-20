import type { RequestEvent } from "@sveltejs/kit";
import makeApiClient from "$lib/api";
import { ApiError, type User } from "$lib/client";

export interface AuthState {
    user: User | null;
    authUnavailable: boolean;
}

/**
 * One authentication lookup per request. Layouts share the promise, so
 * /back/api/people/people/ is called at most once.
 */
export function createAuthStateGetter({
    fetch,
    cookies,
}: Pick<RequestEvent, "fetch" | "cookies">): () => Promise<AuthState> {
    let authStatePromise: Promise<AuthState> | undefined;

    return () => {
        authStatePromise ??= (async () => {
            const api = makeApiClient({ fetch, cookies });
            try {
                const user = await api.me.getCurrentUser();
                return { user, authUnavailable: false };
            } catch (error) {
                if (error instanceof ApiError && error.status < 500) {
                    return { user: { is_authenticated: false }, authUnavailable: false };
                }
                return { user: null, authUnavailable: true };
            }
        })();
        return authStatePromise;
    };
}
