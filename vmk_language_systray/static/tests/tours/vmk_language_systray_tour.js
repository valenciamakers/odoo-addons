/** Copyright 2026 Valencia Makers, SL
 *  License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html). */

import { localization } from "@web/core/l10n/localization";
import { registry } from "@web/core/registry";

/** Fail a tour step, with a message that names what was expected. */
function expect(condition, message) {
    if (!condition) {
        throw new Error(message);
    }
}

const ITEM = ".o_vmk_language_systray";
const MENU = ".o_vmk_language_systray_menu";

// Three languages are active (set up in Python), English the user's own. The
// menu lists them in the order `res.lang.get_installed()` returns.
registry.category("web_tour.tours").add("vmk_language_systray_menu", {
    steps: () => [
        {
            content: "The systray item is there, with its globe icon",
            trigger: `${ITEM} button i.fa.fa-globe`,
            run() {
                const button = document.querySelector(`${ITEM} button`);
                expect(
                    button.getAttribute("aria-label") === "Language: English (US)",
                    `Unexpected aria-label: ${button.getAttribute("aria-label")}`
                );
            },
        },
        {
            content: "Open the dropdown",
            trigger: `${ITEM} button`,
            run: "click",
        },
        {
            content: "Every active language is a radio menu item, the active one checked",
            trigger: `${MENU} [role='menuitemradio']:eq(2)`,
            run() {
                const items = [...document.querySelectorAll(`${MENU} [role='menuitemradio']`)];
                const state = Object.fromEntries(
                    items.map((el) => [el.textContent.trim(), el.getAttribute("aria-checked")])
                );
                const expected = {
                    "English (US)": "true",
                    "Español": "false",
                    "Català": "false",
                    "Français": "false",
                };
                expect(
                    JSON.stringify(Object.entries(state).sort()) ===
                        JSON.stringify(Object.entries(expected).sort()),
                    `Unexpected menu items: ${JSON.stringify(state)}`
                );
            },
        },
        {
            content: "Choose Français",
            trigger: `${MENU} [role='menuitemradio']:contains('Français')`,
            run: "click",
            expectUnloadPage: true,
        },
        {
            content: "The backend reloaded with French active",
            trigger: `${ITEM} button[aria-label*='Français']`,
            run() {
                expect(
                    localization.code === "fr_FR",
                    `The page reloaded in ${localization.code}, not French`
                );
            },
        },
        {
            content: "Open the dropdown again",
            trigger: `${ITEM} button`,
            run: "click",
        },
        {
            content: "French is now the checked one",
            trigger: `${MENU} [role='menuitemradio'][aria-checked='true']:contains('Français')`,
            run() {
                const checked = document.querySelectorAll(
                    `${MENU} [role='menuitemradio'][aria-checked='true']`
                );
                expect(checked.length === 1, `${checked.length} items are checked`);
            },
        },
    ],
});

// Only one language is active, so there is nothing to switch between.
registry.category("web_tour.tours").add("vmk_language_systray_single_language", {
    steps: () => [
        {
            content: "The backend has loaded, with its user menu",
            trigger: ".o_navbar .o_user_menu",
        },
        {
            content: "There is no language item",
            trigger: `.o_navbar:not(:has(${ITEM}))`,
        },
    ],
});
