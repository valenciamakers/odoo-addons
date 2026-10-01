/** @odoo-module **/
/** Copyright 2026 Valencia Makers, SL
 *  License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html). */

import { registry } from "@web/core/registry";
import { user } from "@web/core/user";

// The pinned apps, as in the module's PINNED_LAST: Apps, then Settings.
const PINNED_LAST = ["base.menu_management", "base.menu_administration"];

/** Fail a tour step, with a message that names what was expected. */
function expect(condition, message) {
    if (!condition) {
        throw new Error(message);
    }
}

/** The module's own fold: accents dropped, case ignored. */
function fold(name) {
    return name
        .normalize("NFKD")
        .replace(/\p{M}/gu, "")
        .toLowerCase();
}

/** Apps as `{xmlid, name}`, sorted by the module's rule from their displayed names. */
function expectedOrder(apps) {
    const key = (app) => {
        const pinned = PINNED_LAST.indexOf(app.xmlid);
        return pinned === -1 ? [0, 0, fold(app.name)] : [1, pinned, ""];
    };
    return [...apps].sort((a, b) => {
        const [ka, kb] = [key(a), key(b)];
        for (let i = 0; i < 3; i++) {
            if (ka[i] < kb[i]) return -1;
            if (ka[i] > kb[i]) return 1;
        }
        return 0;
    });
}

/** What the home menu (Enterprise) shows. */
function homeMenuApps() {
    return [...document.querySelectorAll(".o_home_menu .o_apps .o_app")].map((el) => ({
        xmlid: el.dataset.menuXmlid,
        name: el.querySelector(".o_caption").textContent.trim(),
    }));
}

/** What the navbar's apps dropdown (Community) shows. */
function dropdownApps() {
    return [...document.querySelectorAll(".o_popover .o_app[data-menu-xmlid]")].map((el) => ({
        xmlid: el.dataset.menuXmlid,
        name: el.textContent.trim(),
    }));
}

function sameOrder(shown, expected) {
    const names = (apps) => apps.map((app) => app.xmlid).join(", ");
    expect(
        names(shown) === names(expected),
        `Shown: ${shown.map((a) => a.name)}\nExpected: ${expected.map((a) => a.name)}`
    );
}

/** Steps checking the home menu is in the module's order. */
function homeMenuSteps({ stored = false } = {}) {
    return [
        {
            content: "The home menu shows its apps",
            trigger: ".o_home_menu .o_apps .o_app",
            run() {
                const shown = homeMenuApps();
                expect(shown.length >= 5, `Only ${shown.length} apps: ${shown.map((a) => a.name)}`);
                expect(
                    stored === Boolean(user.settings.homemenu_config),
                    `homemenu_config is ${stored ? "unset" : "set"}, expected the opposite`
                );
                sameOrder(shown, expectedOrder(shown));
                const last = shown.slice(-2).map((app) => app.xmlid);
                expect(last.join() === PINNED_LAST.join(), `The last apps are ${last}`);
            },
        },
    ];
}

// Enterprise: the home menu lists the apps alphabetically, Apps and Settings last.
registry.category("web_tour.tours").add("vmk_apps_menu_sort_home_menu", {
    steps: () => homeMenuSteps(),
});

// Enterprise: a stored order of the user's own wins over ours. The test stores it.
registry.category("web_tour.tours").add("vmk_apps_menu_sort_home_menu_stored_order", {
    steps: () => [
        {
            content: "The home menu shows its apps",
            trigger: ".o_home_menu .o_apps .o_app",
            run() {
                const stored = JSON.parse(user.settings.homemenu_config);
                const shown = homeMenuApps();
                const xmlids = shown.map((app) => app.xmlid);
                // Apps named in the stored list come in its order, after any app it omits.
                expect(
                    xmlids.slice(-stored.length).join() === stored.join(),
                    `Shown ${xmlids}, stored ${stored}`
                );
                const ours = expectedOrder(shown).map((app) => app.xmlid);
                expect(xmlids.join() !== ours.join(), "The stored order was ignored");
            },
        },
    ],
});

// Community: the navbar's apps dropdown lists the apps alphabetically.
registry.category("web_tour.tours").add("vmk_apps_menu_sort_navbar", {
    steps: () => [
        {
            content: "Open the apps dropdown",
            trigger: ".o_navbar_apps_menu button",
            run: "click",
        },
        {
            content: "The dropdown lists the apps in order",
            trigger: ".o_popover .o_app[data-menu-xmlid]",
            run() {
                const shown = dropdownApps();
                expect(shown.length >= 5, `Only ${shown.length} apps: ${shown.map((a) => a.name)}`);
                sameOrder(shown, expectedOrder(shown));
            },
        },
    ],
});

// Community: a bare /odoo lands on the first app of the sorted list.
registry.category("web_tour.tours").add("vmk_apps_menu_sort_landing", {
    steps: () => [
        {
            content: "An app is open",
            trigger: ".o_main_navbar .o_menu_brand:not(:empty)",
        },
        {
            content: "Open the apps dropdown",
            trigger: ".o_navbar_apps_menu button",
            run: "click",
        },
        {
            content: "The app open is the first of the sorted list",
            trigger: ".o_popover .o_app[data-menu-xmlid]",
            run() {
                const shown = dropdownApps();
                const first = expectedOrder(shown)[0];
                expect(shown[0].xmlid === first.xmlid, `The first app is ${shown[0].name}`);
                const brand = document.querySelector(".o_main_navbar .o_menu_brand");
                expect(
                    brand.textContent.trim() === first.name,
                    `Landed on ${brand.textContent}, not on ${first.name}`
                );
            },
        },
    ],
});

// Either edition, in Spanish: the order follows the translated names.
registry.category("web_tour.tours").add("vmk_apps_menu_sort_spanish", {
    steps: () => [
        {
            content: "Open the apps dropdown, where there is one",
            trigger: ".o_home_menu .o_app, .o_navbar_apps_menu button",
            run() {
                if (!document.querySelector(".o_home_menu")) {
                    document.querySelector(".o_navbar_apps_menu button").click();
                }
            },
        },
        {
            content: "The apps are in order of their Spanish names",
            trigger: ".o_home_menu .o_app, .o_popover .o_app[data-menu-xmlid]",
            run() {
                const shown = document.querySelector(".o_home_menu")
                    ? homeMenuApps()
                    : dropdownApps();
                const names = shown.map((app) => app.name);
                expect(names[0] === "Abeto", `Not in Spanish: ${names}`);
                sameOrder(shown, expectedOrder(shown));
                // By name Ajustes would precede Aplicaciones; the pinned order keeps Apps first.
                const last = shown.slice(-2).map((app) => app.xmlid);
                expect(last.join() === PINNED_LAST.join(), `Pinned apps are ${last}`);
            },
        },
    ],
});
