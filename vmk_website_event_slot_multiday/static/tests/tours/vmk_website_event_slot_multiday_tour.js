// Copyright 2026 Valencia Makers, SL
// License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

import { registry } from "@web/core/registry";

/**
 * The test starts these tours at an event page with the slot and the days it
 * expects in the URL's fragment, which survives the redirects the event page goes through (`#slot=<id>&from=<weekday>,<day>&to=...`), so
 * the dates can be relative to the day the suite runs: a slot that has begun
 * is no longer offered to visitors.
 *
 * The expected line is matched loosely, since Luxon writes the month, the
 * year, and the space before "PM" as the browser's locale sees fit. What it
 * pins is that each end carries its own weekday and day of the month.
 */
const params = () => new URLSearchParams(window.location.hash.slice(1));
const dayPattern = (weekday, day) => `${weekday}, \\w+\\.? ${day}, \\d{4}, \\d{1,2}:\\d{2}`;

const openSlotModalAndPick = () => [
    {
        content: "Open the registration modal",
        trigger: "button.btn-primary:contains(Register):visible",
        run: "click",
    },
    {
        content: "Pick the slot",
        trigger: `#modal_slot_registration .o_wevent_slot_btn[data-slot-id="${params().get("slot")}"]`,
        run: "click",
    },
];

// A slot from Friday evening to Sunday afternoon names both days.
registry.category("web_tour.tours").add("vmk_website_event_slot_multiday_multiday_slot", {
    steps: () => {
        const [fromWeekday, fromDay] = params().get("from").split(",");
        const [toWeekday, toDay] = params().get("to").split(",");
        const expected = new RegExp(
            `^${dayPattern(fromWeekday, fromDay)}.* - ${dayPattern(toWeekday, toDay)}.*$`
        );
        return [
            ...openSlotModalAndPick(),
            {
                content: "The selected date line names both days",
                trigger: "#modal_slot_registration .o_wevent_selected_slot",
                run() {
                    const text = this.anchor.textContent.trim();
                    if (!expected.test(text)) {
                        throw new Error(`Selected date line "${text}" does not match ${expected}`);
                    }
                },
            },
            {
                content: "The title says a date is selected",
                trigger: "#modal_slot_registration .o_wevent_selected_slot_title:contains(Selected)",
            },
            {
                content: "The slot can be registered for",
                trigger: "#modal_slot_registration .a-submit:enabled",
            },
        ];
    },
});

// A one-day slot keeps core's line: a date and a time, then the end as a time.
registry.category("web_tour.tours").add("vmk_website_event_slot_multiday_one_day_slot", {
    steps: () => {
        const [fromWeekday, fromDay] = params().get("from").split(",");
        const expected = new RegExp(`^${dayPattern(fromWeekday, fromDay)}.* - \\d{1,2}:\\d{2}\\D*$`);
        return [
            ...openSlotModalAndPick(),
            {
                content: "The selected date line is core's",
                trigger: "#modal_slot_registration .o_wevent_selected_slot",
                run() {
                    const text = this.anchor.textContent.trim();
                    if (!expected.test(text)) {
                        throw new Error(`Selected date line "${text}" does not match ${expected}`);
                    }
                },
            },
        ];
    },
});
