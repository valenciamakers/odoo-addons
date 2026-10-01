/** Copyright 2026 Valencia Makers, SL
 *  License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html). */

import { rpc } from "@web/core/network/rpc";
import { registry } from "@web/core/registry";

/** Fail a tour step, with a message that names what was expected. */
function expect(actual, expected, what) {
    if (JSON.stringify(actual) !== JSON.stringify(expected)) {
        throw new Error(
            `${what}: expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`
        );
    }
}

/**
 * The module's own comparison, written again here so that the tour checks the
 * module against its promise instead of against its own code: accents and case
 * ignored, then plain code-point order. (`localeCompare` would also ignore
 * spaces and punctuation, which the module does not.)
 */
function folded(label) {
    return label
        .normalize("NFKD")
        .replace(/[̀-ͯ]/g, "")
        .toLowerCase();
}

function byFoldedLabel(a, b) {
    const x = folded(a);
    const y = folded(b);
    return x < y ? -1 : x > y ? 1 : 0;
}

/** The sidebar entries of the Settings screen, as displayed. */
function sidebarTabs() {
    return [...document.querySelectorAll(".o_setting_container .settings_tab .tab")].map((el) => ({
        key: el.dataset.key,
        label: el.querySelector(".app_name").textContent.trim(),
    }));
}

/**
 * Click a sidebar entry and check that its own settings are what opens.
 * `selector` picks the entry; it is compared with what the screen then shows.
 */
function openTab(selector, name) {
    let clicked;
    return [
        {
            content: `Click the ${name} sidebar entry`,
            trigger: `.o_setting_container .settings_tab ${selector}`,
            async run(helpers) {
                clicked = {
                    key: helpers.anchor.dataset.key,
                    label: helpers.anchor.querySelector(".app_name").textContent.trim(),
                };
                // Mark the entry: the entry already selected, General Settings at
                // first, satisfies a bare `.selected` before the click has rendered.
                for (const tab of document.querySelectorAll("[data-vmk-clicked]")) {
                    delete tab.dataset.vmkClicked;
                }
                helpers.anchor.dataset.vmkClicked = "1";
                await helpers.click();
            },
        },
        {
            content: `The ${name} entry is selected and its own settings are shown`,
            trigger: ".settings_tab .tab.selected[data-vmk-clicked]",
            run() {
                const selected = document.querySelector(".settings_tab .tab.selected");
                expect(selected.dataset.key, clicked.key, "Selected entry");
                const blocks = [...document.querySelectorAll(".settings .app_settings_block")];
                expect(
                    blocks.map((b) => b.dataset.key),
                    [clicked.key],
                    "Settings blocks on screen"
                );
                expect(blocks[0].getAttribute("string"), clicked.label, "Title of the block");
            },
        },
    ];
}

function sidebarSteps({ translated } = {}) {
    return [
        {
            content: "The Settings screen lists several apps in its sidebar",
            trigger: ".o_setting_container .settings_tab .tab:eq(3)",
            run() {
                const tabs = sidebarTabs();
                expect(tabs[0].key, "general_settings", "First entry");
                const rest = tabs.slice(1).map((t) => t.label);
                if (translated && !rest.includes(translated)) {
                    throw new Error(`No section is labelled ${translated}: ${rest}`);
                }
                expect(rest, [...rest].sort(byFoldedLabel), "Sidebar order after General Settings");
            },
        },
        // The first entry after General Settings, the last one, and General Settings.
        ...openTab(".tab:eq(1)", "second"),
        ...openTab(".tab:last", "last"),
        ...openTab(".tab:first", "General Settings"),
    ];
}

registry.category("web_tour.tours").add("vmk_settings_sort_sidebar", {
    steps: () => sidebarSteps(),
});

registry.category("web_tour.tours").add("vmk_settings_sort_sidebar_translated", {
    // The Mango section the test adds is Abeto in Spanish, which moves it.
    steps: () => sidebarSteps({ translated: "Abeto" }),
});

registry.category("web_tour.tours").add("vmk_settings_sort_no_technical", {
    steps: () => [
        {
            content: "The sidebar is sorted without developer mode too",
            trigger: ".o_setting_container .settings_tab .tab:eq(3)",
            run() {
                const rest = sidebarTabs().slice(1).map((t) => t.label);
                expect(rest, [...rest].sort(byFoldedLabel), "Sidebar order");
            },
        },
        {
            content: "Settings has its own menus in the navbar, and no Technical one",
            trigger: ".o_navbar .o_menu_sections .dropdown-toggle",
            run() {
                const sections = [
                    ...document.querySelectorAll(".o_navbar .o_menu_sections .dropdown-toggle"),
                ].map((el) => el.textContent.trim());
                if (sections.includes("Technical")) {
                    throw new Error(`Technical is offered outside developer mode: ${sections}`);
                }
            },
        },
    ],
});

registry.category("web_tour.tours").add("vmk_settings_sort_technical", {
    steps: () => [
        {
            content: "Open the Technical menu",
            trigger: ".o_navbar .o_menu_sections .dropdown-toggle:contains('Technical')",
            run: "click",
        },
        {
            content: "Its groupings are in alphabetical order",
            trigger: ".o-dropdown--menu .dropdown-header:eq(3)",
            run() {
                const headers = [
                    ...document.querySelectorAll(".o-dropdown--menu .dropdown-header"),
                ].map((el) => el.textContent.trim());
                expect(headers, [...headers].sort(byFoldedLabel), "Technical groupings");
            },
        },
        {
            content: "Inside each grouping, the entries keep their own sequence",
            trigger: ".o-dropdown--menu .dropdown-header:eq(3)",
            async run() {
                // Entries follow their header in the DOM. Their order must be the
                // model's own, `sequence, id`: the module leaves it alone.
                const groups = [];
                for (const el of document.querySelectorAll(".o-dropdown--menu > *")) {
                    if (el.classList.contains("dropdown-header")) {
                        groups.push({ name: el.textContent.trim(), ids: [] });
                    } else if (groups.length && el.dataset.section) {
                        groups.at(-1).ids.push(parseInt(el.dataset.section));
                    }
                }
                let checked = 0;
                for (const group of groups) {
                    if (group.ids.length < 2) {
                        continue;
                    }
                    const rows = await rpc("/web/dataset/call_kw/ir.ui.menu/search_read", {
                        model: "ir.ui.menu",
                        method: "search_read",
                        args: [[["id", "in", group.ids]], ["id"]],
                        kwargs: { order: "sequence, id" },
                    });
                    expect(
                        group.ids,
                        rows.map((r) => r.id),
                        `Entries of ${group.name}`
                    );
                    checked++;
                }
                if (checked < 2) {
                    throw new Error("Fewer than two groupings had entries to compare");
                }
            },
        },
    ],
});
