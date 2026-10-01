// Copyright 2026 Valencia Makers, SL
// License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

import { registry } from "@web/core/registry";
import * as hoot from "@odoo/hoot-dom";

// Prefixed with `body`: a picker opened from inside a dialog lives in its own
// overlay, which the tour runner cannot tell from one behind the dialog and
// refuses to act on; a selector starting with `body` skips that check.
const PICKER = "body .o_popover .o_datetime_picker";

const SLOT_COUNT = "button[name=action_open_slot_calendar]";

/**
 * Open the slot calendar from one of the event form's two slot counts. On a
 * bare install both are on show. With enough apps installed the Slots button
 * at the top moves under More, and another module may move the count beside
 * Multiple Slots onto a tab, which a notebook draws only once it is open: so
 * where no count is on show, More is opened, then each tab in turn.
 */
const openSlotCalendar = [
    {
        content: "Find a slot count, under More or on whichever tab holds it",
        trigger: ".o_form_view .o_notebook",
        async run() {
            const onShow = () =>
                [...document.querySelectorAll(SLOT_COUNT)].some((button) => button.offsetParent);
            const places = [
                null,
                document.querySelector(".o-form-buttonbox .o_button_more"),
                ...document.querySelectorAll(".o_notebook .nav-link"),
            ];
            for (const place of places) {
                if (place) {
                    await hoot.click(place);
                    await hoot.animationFrame();
                }
                if (onShow()) {
                    return;
                }
            }
            throw new Error("The event form shows no slot count anywhere");
        },
    },
    {
        content: "Open the slot calendar from the event",
        trigger: `${SLOT_COUNT}:visible`,
        run: "click",
    },
];

/**
 * With the range picker open: click a first day, then a last one, set both
 * times, and close it with Apply. Days are the day-of-month numbers of the
 * month the picker shows; `:not(.o_out_of_range)` keeps the greyed-out days
 * of the neighbouring months from matching the same number.
 */
const pickRange = ({ from, to, startTime, endTime }) => [
    {
        content: "The range picker opens",
        trigger: PICKER,
    },
    {
        content: `Start the range on the ${from}th`,
        trigger: `${PICKER} .o_date_item_cell:not(.o_out_of_range):text(${from})`,
        run: "click",
    },
    {
        content: `End the range on the ${to}th`,
        trigger: `${PICKER} .o_date_item_cell:not(.o_out_of_range):text(${to})`,
        run: "click",
    },
    {
        content: "Set the start time",
        trigger: `${PICKER} .o_time_picker_input:eq(0)`,
        run: `edit ${startTime}`,
    },
    {
        content: "Set the end time",
        trigger: `${PICKER} .o_time_picker_input:eq(1)`,
        run: `edit ${endTime}`,
    },
    {
        content: "Apply the range",
        trigger: `${PICKER} .btn-primary:contains(Apply)`,
        run: "click",
    },
    {
        content: "The picker closes",
        trigger: `body:not(:has(${PICKER}))`,
    },
];

/** Pick a day by its date in the slot calendar's month view. */
const dayCell = (isoDate) => `.o_calendar_widget .fc-day[data-date="${isoDate}"]`;

// An existing one-day slot is given a three-day range on its own form.
registry.category("web_tour.tours").add("vmk_event_slot_multiday_edit_range", {
    steps: () => [
        {
            // 18:00 in New York is 22:00 in the test browser's UTC: showing
            // the viewer's own time instead of the event's would read 22:00.
            content: "The slot form shows the range in the event's time",
            trigger: ".o_form_view .o_field_vmk_event_slot_daterange .o_daterange_start",
            run() {
                // A button on a saved record, reading in the language's own clock.
                const shown = this.anchor.value || this.anchor.textContent;
                if (!/\b(0?6:00(:00)?\s?PM|18:00(:00)?)/i.test(shown)) {
                    throw new Error(`The range starts "${shown}", not at 18:00 as in New York`);
                }
            },
        },
        {
            content: "Open the range widget's picker",
            trigger: ".o_form_view .o_field_vmk_event_slot_daterange .o_daterange_start",
            run: "click",
        },
        ...pickRange({ from: 9, to: 11, startTime: "18:00", endTime: "13:00" }),
        {
            content: "Save the slot",
            trigger: ".o_form_button_save",
            run: "click",
        },
        {
            content: "The slot is saved",
            trigger: ".o_form_saved, .o_form_readonly",
        },
    ],
});

// A new slot is made from the slot calendar's New button, in a dialog.
registry.category("web_tour.tours").add("vmk_event_slot_multiday_calendar_new", {
    steps: () => [
        ...openSlotCalendar,
        {
            content: "Wait for the slot calendar",
            trigger: ".o_calendar_view .o_calendar_widget .fc-day",
        },
        {
            content: "Click New",
            trigger: ".o-calendar-button-new",
            run: "click",
        },
        {
            content: "The dialog shows the range widget; open its picker",
            // A new slot has no range yet, so the start is an input, not a button.
            trigger:
                ".modal .o_field_vmk_event_slot_daterange input[data-field=start_datetime], " +
                ".modal .o_field_vmk_event_slot_daterange .o_daterange_start",
            run: "click",
        },
        {
            content: "Choose the range mode, for a slot without a range yet",
            isActive: [`${PICKER} .o_toggle_range:not(.active)`],
            trigger: `${PICKER} .o_toggle_range:contains(Range)`,
            run: "click",
        },
        ...pickRange({ from: 16, to: 18, startTime: "17:30", endTime: "11:15" }),
        {
            content: "Save the new slot",
            trigger: ".modal .o_form_button_save, .modal footer .btn-primary",
            run: "click",
        },
        {
            content: "The dialog closes and the slot is drawn",
            trigger: `body:not(:has(.modal)) .o_calendar_widget .fc-event`,
        },
    ],
});

// Select days in the calendar and add one single-day slot to each.
registry.category("web_tour.tours").add("vmk_event_slot_multiday_calendar_multi_create", {
    steps: () => [
        ...openSlotCalendar,
        {
            content: "Select the 13th",
            trigger: dayCell("2026-10-13"),
            run: "click",
        },
        {
            content: "Add the 14th to the selection, with Ctrl held",
            trigger: dayCell("2026-10-14"),
            async run({ click }) {
                await hoot.keyDown("Control");
                await click(dayCell("2026-10-14"));
                await hoot.keyUp("Control");
            },
        },
        {
            // The box counts existing slots under the selection, so on two
            // empty days it reads "0 selected": check the days instead.
            content: "Both days are highlighted and the Add button shows",
            trigger: `${dayCell("2026-10-13")}.o-highlight, ${dayCell("2026-10-14")}.o-highlight`,
        },
        {
            content: "The selection box is shown",
            trigger: ".o_multi_selection_buttons",
        },
        {
            content: "Click Add",
            trigger: ".o_multi_selection_buttons button.btn-primary:contains(Add)",
            run: "click",
        },
        {
            content: "Set the start time",
            trigger: ".o_multi_create_popover .o_time_picker_input:eq(0)",
            run: "edit 10:00",
        },
        {
            content: "Set the end time",
            trigger: ".o_multi_create_popover .o_time_picker_input:eq(1)",
            run: "edit 12:30",
        },
        {
            content: "Create the slots",
            trigger: ".o_multi_create_popover .popover-footer .btn-primary",
            run: "click",
        },
        {
            content: "Both slots are drawn",
            trigger: `body:not(:has(.o_multi_create_popover)) ${dayCell("2026-10-14")} .fc-event`,
        },
    ],
});
