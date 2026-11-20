import { writable } from "svelte/store";
import en from "$lib/locales/en.json";
import es from "$lib/locales/es.json";
import fr from "$lib/locales/fr.json";

export type Lang = "en" | "es" | "fr";

const catalogs: Record<Lang, Record<string, string>> = { en, es, fr };

export const lang = writable<Lang>("en");

export function translate(code: Lang, key: string, vars: Record<string, string> = {}): string {
    const catalog = catalogs[code] ?? catalogs.en;
    let text = catalog[key] ?? catalogs.en[key] ?? key;
    for (const [name, value] of Object.entries(vars)) {
        text = text.replaceAll(`{${name}}`, value);
    }
    return text;
}

export function countLabel(code: Lang, count: number, readableName: string): string {
    return translate(code, "numberofitems", {
        number: String(count),
        readablename: readableName,
    });
}
