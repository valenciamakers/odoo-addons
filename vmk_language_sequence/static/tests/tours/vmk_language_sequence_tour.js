/** Copyright 2026 Valencia Makers, SL
 *  License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html). */

import * as hoot from "@odoo/hoot-dom";
import { registry } from "@web/core/registry";

/** Fail a tour step, with a message that names what was expected. */
function expect(actual, expected, what) {
    if (JSON.stringify(actual) !== JSON.stringify(expected)) {
        throw new Error(
            `${what}: expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`
        );
    }
}

// Sequences are set in Python so that the order is not alphabetical:
// Français, English (US), Català, Español.

registry.category("web_tour.tours").add("vmk_language_sequence_systray", {
    steps: () => [
        {
            content: "Open the language menu of vmk_language_systray",
            trigger: ".o_vmk_language_systray button",
            run: "click",
        },
        {
            content: "The menu lists the languages in their sequence, not by name",
            trigger: ".o_vmk_language_systray_menu [role='menuitemradio']:eq(3)",
            run() {
                const names = [
                    ...document.querySelectorAll(
                        ".o_vmk_language_systray_menu [role='menuitemradio']"
                    ),
                ].map((el) => el.textContent.trim());
                expect(names, ["Français", "English (US)", "Català", "Español"], "Menu order");
            },
        },
    ],
});

registry.category("web_tour.tours").add("vmk_language_sequence_website_selector", {
    url: "/",
    steps: () => [
        {
            content: "The website's language selector lists the languages in their sequence",
            trigger: ".js_language_selector .js_change_lang:not(:visible):eq(3), .js_language_selector .js_change_lang:eq(3)",
            run() {
                // The layout carries more than one selector (header, footer); the
                // first is enough, and they are the same template.
                const codes = [
                    ...document
                        .querySelector(".js_language_selector")
                        .querySelectorAll(".js_change_lang"),
                ].map((el) => el.dataset.url_code);
                expect(codes, ["fr", "en", "ca_ES", "es"], "Selector order");
            },
        },
    ],
});

registry.category("web_tour.tours").add("vmk_language_sequence_translation_dialog", {
    steps: () => [
        {
            // The translate button is hidden until its field is hovered or focused.
            content: "Focus the country's name",
            trigger: ".o_field_widget[name='name'] input",
            run: "click",
        },
        {
            content: "Open the translation dialog of the name",
            trigger: ".o_field_widget[name='name'] .o-translate-button",
            run: "click",
        },
        {
            content: "After the user's own language, the dialog follows the sequence",
            trigger: ".o_translation_dialog label:eq(3)",
            run() {
                const names = [...document.querySelectorAll(".o_translation_dialog label")].map(
                    (el) => el.textContent.trim()
                );
                // The dialog itself puts the user's language, English, first.
                expect(
                    names,
                    ["English (US)", "French / Français", "Catalan / Català", "Spanish / Español"],
                    "Dialog order"
                );
            },
        },
        {
            content: "Close the dialog",
            trigger: ".o_translation_dialog footer .btn-secondary",
            run: "click",
        },
        {
            content: "The dialog is gone",
            trigger: "body:not(:has(.o_translation_dialog))",
        },
    ],
});

registry.category("web_tour.tours").add("vmk_language_sequence_drag", {
    steps: () => [
        {
            content: "The Languages list shows the enabled languages first, in sequence",
            trigger: ".o_list_view .o_data_row:eq(3)",
            run() {
                const names = [...document.querySelectorAll(".o_data_row")]
                    .slice(0, 4)
                    .map((row) => row.querySelector("[name='name']").textContent.trim());
                expect(
                    names,
                    ["French / Français", "English (US)", "Catalan / Català", "Spanish / Español"],
                    "List order before the drag"
                );
            },
        },
        {
            content: "Drag French below Catalan by its handle",
            trigger: ".o_data_row:eq(0) .o_row_handle",
            async run(helpers) {
                const target = document.querySelectorAll(".o_data_row")[2];
                const { drop, moveTo } = await hoot.drag(helpers.anchor);
                await hoot.animationFrame();
                // A first move, past the tolerance and still over the dragged row, starts the
                // drag. Sortable binds its pointerenter listeners at that moment, so a single
                // move straight onto the target would arrive too late to be heard.
                await moveTo(helpers.anchor, { position: { top: 20, left: 20 }, relative: true });
                await hoot.animationFrame();
                await moveTo(target, { position: "bottom", relative: true });
                await hoot.animationFrame();
                await drop();
                await hoot.animationFrame();
            },
        },
        {
            content: "The list shows the new order",
            trigger: ".o_data_row:eq(2):contains('French')",
            run() {
                const names = [...document.querySelectorAll(".o_data_row")]
                    .slice(0, 4)
                    .map((row) => row.querySelector("[name='name']").textContent.trim());
                expect(
                    names,
                    ["English (US)", "Catalan / Català", "French / Français", "Spanish / Español"],
                    "List order after the drag"
                );
            },
        },
    ],
});
