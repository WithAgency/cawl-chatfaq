import { redirect } from "@sveltejs/kit";
import type { PageServerLoad } from "./$types";
import makeApiClient from "$lib/api";

export const load: PageServerLoad = async ({ fetch, cookies, url }) => {
    const api = makeApiClient({ fetch, cookies });
    try {
        await api.auth.logout();
    } catch {
        // An already anonymous session still leaves the login page.
    }
    cookies.delete("token", { path: "/", secure: url.protocol === "https:" });
    redirect(303, "/login");
};
