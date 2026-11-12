// Copyright 2026 Valencia Makers, SL
// License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

import { registry } from "@web/core/registry";

const tours = registry.category("web_tour.tours");

const PURPLE = ".o_list_renderer .o_data_row:nth-child(6)";

// From General Settings to the list, renaming Purple and choosing another
// color for it.
tours.add("vmk_colorlist_colors_edit_tour", {
    steps: () => [
        {
            content: "the setting has its label and its help",
            trigger: `#vmk_colorlist_colors_setting:has(.o_form_label:contains("Custom Colors")) .text-muted:contains("Set the colors used for tags, cards, calendars, etc.")`,
        },
        {
            content: "open the list from General Settings",
            trigger: `#vmk_colorlist_colors_setting button:contains("Edit Colors")`,
            run: "click",
        },
        {
            content: "the list has Odoo's twelve colors",
            trigger: ".o_list_renderer .o_data_row:nth-child(12):last-child",
        },
        {
            content: "each color starts with Odoo's name, and no reset button",
            trigger: `${PURPLE}:not(:has(button[name='action_reset'])) td[name='name']:contains("Purple")`,
        },
        {
            content: "No color cannot be renamed",
            trigger: ".o_list_renderer .o_data_row:nth-child(1) td[name='name'].o_readonly_modifier",
        },
        {
            content: "edit Purple's row",
            trigger: `${PURPLE} td[name='name']`,
            run: "click",
        },
        {
            content: "rename it",
            trigger: `${PURPLE} td[name='name'] input`,
            run: "edit Brand",
        },
        {
            // The browser's own color input sits invisible (opacity 0) over
            // the swatch, so the step finds the swatch and sets the input.
            content: "choose a color with the picker",
            trigger: `${PURPLE} td[name='color'] .o_field_color:has(input[type='color'])`,
            run() {
                const input = this.anchor.querySelector("input[type='color']");
                input.value = "#7b2cbf";
                input.dispatchEvent(new Event("input", { bubbles: true }));
                input.dispatchEvent(new Event("change", { bubbles: true }));
            },
        },
        {
            content: "save",
            trigger: ".o_list_button_save",
            run: "click",
        },
        {
            content: "the row shows the new name, and a button to put Odoo's back",
            trigger: `${PURPLE}:not(.o_selected_row) td[name='name']:contains("Brand")`,
        },
        {
            content: "the reset button's tooltip says what it does",
            trigger: `${PURPLE} button[name='action_reset'][data-tooltip="Reset to default values"]`,
        },
    ],
});

// The reset button on a row puts Odoo's color and name back, and reloads.
tours.add("vmk_colorlist_colors_reset_tour", {
    steps: () => [
        {
            content: "Purple is custom",
            trigger: `${PURPLE} td[name='name']:contains("Brand")`,
        },
        {
            content: "reset it",
            trigger: `${PURPLE} button[name='action_reset']`,
            run: "click",
            expectUnloadPage: true,
        },
        {
            content: "after the reload, the row has Odoo's name back, and no reset button",
            trigger: `${PURPLE}:not(:has(button[name='action_reset'])) td[name='name']:contains("Purple")`,
        },
    ],
});

// Elsewhere in the backend, a color picker takes the new name and the new
// color: a contact tag colored Purple.
tours.add("vmk_colorlist_colors_picker_tour", {
    steps: () => [
        {
            content: "the tag's color button is named after the renamed color",
            trigger: `.o_data_row:contains("VMK test tag") .o_colorlist_toggler[title="Brand"]`,
        },
        {
            content: "and drawn in the chosen color",
            trigger: `.o_data_row:contains("VMK test tag") .o_colorlist_toggler.o_colorlist_item_color_5`,
            run() {
                const color = getComputedStyle(this.anchor).backgroundColor;
                if (color !== "rgb(123, 44, 191)") {
                    throw new Error(`The swatch is ${color}, not the chosen color.`);
                }
            },
        },
    ],
});
