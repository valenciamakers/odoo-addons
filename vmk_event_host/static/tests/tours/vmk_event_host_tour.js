/** @odoo-module **/
// Copyright 2026 Valencia Makers, SL
// License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

import { registry } from "@web/core/registry";
import { stepUtils } from "@web_tour/tour_service/tour_utils";

const tours = registry.category("web_tour.tours");

// The summary button reads the hosts in the order set on the Hosts tab and
// opens that tab.
tours.add("vmk_event_host_summary_tour", {
    steps: () => [
        {
            content: "the summary lists the hosts in their own order, not alphabetically",
            trigger: `.o_field_widget[name="vmk_host_names"] button.vmk_field_as_text:contains("Zoe Zapata (Lead), Ada Lovelace")`,
        },
        {
            content: "its accessible name says what it does, not only what it reads",
            trigger: `button.vmk_field_as_text[aria-label="Zoe Zapata (Lead), Ada Lovelace — show the Hosts tab"]`,
        },
        {
            content: "the Hosts tab is not the active one yet",
            trigger: `.o_notebook .nav-link[name="vmk_hosts"]:not(.active)`,
        },
        {
            content: "click the summary",
            trigger: "button.vmk_field_as_text",
            run: "click",
        },
        {
            content: "the Hosts tab is now active",
            trigger: `.o_notebook .nav-link.active[name="vmk_hosts"]`,
        },
        {
            content: "and its lines are on screen",
            trigger: `.o_field_widget[name="vmk_host_ids"] .o_data_row:contains("Ada Lovelace")`,
        },
    ],
});

// Adding a host line from the Hosts tab.
tours.add("vmk_event_host_add_tour", {
    steps: () => [
        {
            content: "open the Hosts tab",
            trigger: `.o_notebook .nav-link[name="vmk_hosts"]`,
            run: "click",
        },
        {
            content: "add a line",
            trigger: `.o_field_widget[name="vmk_host_ids"] .o_field_x2many_list_row_add a`,
            run: "click",
        },
        {
            content: "type the host's name",
            trigger: `.o_field_widget[name="vmk_host_ids"] .o_selected_row div[name="partner_id"] input`,
            run: "edit Grace",
        },
        {
            content: "pick the suggestion",
            trigger: `.o-autocomplete--dropdown-item:contains("Grace Hopper")`,
            run: "click",
        },
        {
            content: "give the role",
            trigger: `.o_field_widget[name="vmk_host_ids"] .o_selected_row div[name="role"] input`,
            run: "edit Guest speaker",
        },
        ...stepUtils.saveForm(),
        {
            content: "the summary now ends with the new host",
            trigger: `button.vmk_field_as_text:contains("Zoe Zapata (Lead), Ada Lovelace, Grace Hopper (Guest speaker)")`,
        },
    ],
});

// Dragging a line by its handle reorders the hosts, and with them the summary.
tours.add("vmk_event_host_reorder_tour", {
    steps: () => [
        {
            content: "open the Hosts tab",
            trigger: `.o_notebook .nav-link[name="vmk_hosts"]`,
            run: "click",
        },
        {
            content: "drag the first host below the second",
            trigger: `.o_field_widget[name="vmk_host_ids"] .o_data_row:eq(0) .o_row_handle`,
            // 18's helper reads its own anchor through `this`, so it is called
            // on the helpers object, not destructured.
            async run(helpers) {
                await helpers.drag_and_drop(
                    ".o_field_widget[name='vmk_host_ids'] .o_data_row:contains('Ada Lovelace'):visible",
                    { position: "bottom", relative: true }
                );
            },
        },
        {
            content: "the list shows the new order",
            trigger: `.o_field_widget[name="vmk_host_ids"] .o_data_row:eq(0):contains("Ada Lovelace")`,
        },
        ...stepUtils.saveForm(),
        {
            content: "the summary follows",
            trigger: `button.vmk_field_as_text:contains("Ada Lovelace, Zoe Zapata (Lead)")`,
        },
    ],
});

// Searching the event list by host.
tours.add("vmk_event_host_search_tour", {
    steps: () => [
        {
            content: "wait for the list",
            trigger: ".o_list_view .o_data_row:contains('Soldering Basics')",
        },
        {
            content: "type a host's name in the search bar",
            trigger: ".o_searchview_input",
            run: "edit Ada",
        },
        {
            content: "choose the Host entry",
            trigger: `.o_searchview_autocomplete .o_menu_item:contains("Host")`,
            run: "click",
        },
        {
            content: "the event she hosts is listed",
            trigger: ".o_list_view .o_data_row:contains('Intro to 3D Printing')",
        },
        {
            content: "and so is the other one she hosts",
            trigger: ".o_list_view .o_data_row:contains('Soldering Basics')",
        },
        {
            content: "the event without her is gone",
            trigger: ".o_list_view:not(:has(.o_data_row:contains('CNC Night')))",
        },
    ],
});

// Grouping the event list by host: an event with two hosts appears under both.
tours.add("vmk_event_host_group_tour", {
    steps: () => [
        {
            content: "wait for the list",
            trigger: ".o_list_view .o_data_row:contains('Soldering Basics')",
        },
        {
            content: "open the search options",
            trigger: ".o_searchview_dropdown_toggler",
            run: "click",
        },
        {
            content: "group by Host",
            trigger: `.o_group_by_menu .o-dropdown-item:contains("Host")`,
            run: "click",
        },
        {
            content: "Ada's group holds both her events",
            trigger: `.o_list_view .o_group_header:contains("Ada Lovelace"):contains("(2)")`,
        },
        {
            content: "Zoe's holds one",
            trigger: `.o_list_view .o_group_header:contains("Zoe Zapata"):contains("(1)")`,
        },
        {
            content: "and the event with no host is under None",
            trigger: `.o_list_view .o_group_header:contains("None"):contains("(1)")`,
        },
    ],
});
