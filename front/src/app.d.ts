import type { AuthState } from "$lib/auth.server";

declare global {
    namespace App {
        interface Locals {
            getAuthState: () => Promise<AuthState>;
        }
        interface PageData {
            user?: {
                is_authenticated?: boolean;
                first_name?: string;
                last_name?: string;
                email?: string;
            } | null;
            useRay?: boolean;
        }
    }
}

export {};
