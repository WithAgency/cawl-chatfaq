import { error, redirect } from "@sveltejs/kit";
import type { LayoutServerLoad } from "./$types";

export const load: LayoutServerLoad = async ({ locals, fetch }) => {
    const { user, authUnavailable } = await locals.getAuthState();

    if (authUnavailable) {
        error(503, "Authentication service unavailable");
    }

    if (!user?.is_authenticated) {
        redirect(307, "/login");
    }

    let useRay = false;
    try {
        const response = await fetch("http://api/back/api/language-model/ray-status/");
        if (response.ok) {
            useRay = Boolean((await response.json()).use_ray);
        }
    } catch {
        useRay = false;
    }

    return { user, useRay };
};
