import { fail, redirect } from "@sveltejs/kit";
import type { Actions } from "./$types";

export const actions: Actions = {
    default: async ({ request, fetch, cookies, url }) => {
        const data = await request.formData();
        const email = String(data.get("email") ?? "");
        const password = String(data.get("password") ?? "");
        const response = await fetch("http://api/back/api/login/", {
            method: "POST",
            headers: {
                Authorization: `Basic ${btoa(`${email}:${password}`)}`,
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ rememberme: data.get("remember") === "on" }),
        });

        if (!response.ok) {
            return fail(400, { error: "Invalid email or password" });
        }

        const body = await response.json();
        cookies.set("token", body.token, {
            path: "/",
            httpOnly: false,
            sameSite: "lax",
            secure: url.protocol === "https:",
        });
        redirect(303, "/");
    },
};
