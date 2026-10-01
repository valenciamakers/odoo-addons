// Copyright 2026 Valencia Makers, SL
// License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

import { registry } from "@web/core/registry";
import { stepUtils } from "@web_tour/tour_utils";

const tours = registry.category("web_tour.tours");

const OPEN_TAB = {
    content: "open the Additional Emails tab",
    trigger: `.o_notebook .nav-link[name="vmk_additional_emails"]`,
    run: "click",
};
const LIST = `.o_field_widget[name="vmk_email_ids"]`;

// Adding an additional address from the tab.
tours.add("vmk_partner_email_multiple_add_tour", {
    steps: () => [
        OPEN_TAB,
        {
            content: "add an address",
            trigger: `${LIST} .o_field_x2many_list_row_add a`,
            run: "click",
        },
        {
            content: "type it",
            trigger: `${LIST} .o_selected_row div[name="email"] input`,
            run: "edit alice.billing@example.com",
        },
        {
            content: "label it",
            trigger: `${LIST} .o_selected_row div[name="label"] input`,
            run: "edit billing",
        },
        ...stepUtils.saveForm(),
        {
            content: "the saved row is listed",
            trigger: `${LIST} .o_data_row:contains("alice.billing@example.com"):contains("billing")`,
        },
    ],
});

// The swap button exchanges the primary address with the row's.
tours.add("vmk_partner_email_multiple_swap_tour", {
    steps: () => [
        OPEN_TAB,
        {
            content: "the swap button is named for what it does, although its text is hidden",
            trigger: `${LIST} .o_data_row:contains("alice.work@example.com") button[name="action_promote_to_primary"]`,
            run() {
                const name = this.anchor.textContent.trim();
                const expected = "Swap with the contact's primary email address";
                if (name !== expected) {
                    throw new Error(`accessible name is "${name}", expected "${expected}"`);
                }
                const label = this.anchor.querySelector("span");
                const box = label.getBoundingClientRect();
                if (box.width > 1 || box.height > 1) {
                    throw new Error("the text label is not visually hidden");
                }
                if (!this.anchor.querySelector(".fa-exchange")) {
                    throw new Error("the fa-exchange icon is missing");
                }
            },
        },
        {
            content: "press it",
            trigger: `${LIST} .o_data_row:contains("alice.work@example.com") button[name="action_promote_to_primary"]`,
            run: "click",
        },
        {
            content: "the primary field now holds the former additional address",
            trigger: `.o_field_widget[name="email"] input:value("alice.work@example.com")`,
        },
        {
            content: "and the row holds the former primary",
            trigger: `${LIST} .o_data_row:contains("alice@example.com")`,
        },
    ],
});

// The readonly cell of the list: address as text, envelope as a mailto link.
tours.add("vmk_partner_email_multiple_link_tour", {
    steps: () => [
        OPEN_TAB,
        {
            content: "the row shows the address as plain text, not as a link",
            trigger: `${LIST} .o_data_row:contains("alice.work@example.com") .o_data_cell[name="email"] span.o_text_overflow:contains("alice.work@example.com")`,
        },
        {
            content: "the envelope links to it, hidden until the row is hovered or focused",
            // Hoot counts opacity: 0 as not visible, hence the explicit :not(:visible).
            trigger: `${LIST} .o_data_row:contains("alice.work@example.com") a.vmk_email_send:not(:visible)`,
            run() {
                if (this.anchor.getAttribute("href") !== "mailto:alice.work@example.com") {
                    throw new Error(`unexpected href ${this.anchor.getAttribute("href")}`);
                }
                if (getComputedStyle(this.anchor).opacity !== "0") {
                    throw new Error("the envelope is visible before the row is focused");
                }
            },
        },
        {
            content: "tab to the envelope: focus reveals it",
            trigger: `${LIST} .o_data_row:contains("alice.work@example.com") a.vmk_email_send:not(:visible)`,
            run() {
                this.anchor.focus();
            },
        },
        {
            content: "it is now fully opaque, and still the same link",
            trigger: `${LIST} .o_data_row:contains("alice.work@example.com") a.vmk_email_send:visible`,
            run() {
                if (this.anchor.getAttribute("href") !== "mailto:alice.work@example.com") {
                    throw new Error("the revealed envelope lost its link");
                }
            },
        },
    ],
});

// The contact search finds a contact by one of its additional addresses.
tours.add("vmk_partner_email_multiple_search_tour", {
    steps: () => [
        {
            content: "wait for the list",
            trigger: `.o_list_view .o_data_row:contains("Bob Builder")`,
        },
        {
            content: "type an additional address in the search bar",
            trigger: ".o_searchview_input",
            run: "edit alice.work@example.com",
        },
        {
            content: "search the Email entry",
            trigger: `.o_searchview_autocomplete .o-dropdown-item:contains("Email")`,
            run: "click",
        },
        {
            content: "the contact holding it is listed",
            trigger: `.o_list_view .o_data_row:contains("Alice Example")`,
        },
        {
            content: "and the others are not",
            trigger: `.o_list_view:not(:has(.o_data_row:contains("Bob Builder")))`,
        },
    ],
});

// A many2one to contacts finds one by an additional address.
tours.add("vmk_partner_email_multiple_autocomplete_tour", {
    steps: () => [
        {
            content: "type an additional address into the Company field",
            trigger: `.o_field_widget[name="parent_id"] input`,
            run: "edit alice.work@example.com",
        },
        {
            content: "the contact holding it is suggested",
            trigger: `.o-autocomplete--dropdown-item:contains("Alice Example")`,
            run: "click",
        },
        {
            content: "and is selected",
            trigger: `.o_field_widget[name="parent_id"] input:value("Alice Example")`,
        },
        ...stepUtils.discardForm(),
    ],
});
