import { redirect } from "@sveltejs/kit";
import type { LayoutServerLoad } from "./$types";

export const load: LayoutServerLoad = async ({ locals }) => {
    const { user } = await locals.getAuthState();
    if (user?.is_authenticated) {
        redirect(303, "/");
    }
    return {};
};
