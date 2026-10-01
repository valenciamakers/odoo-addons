// Copyright 2026 Valencia Makers, SL
// License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

import { registry } from "@web/core/registry";
import { stepUtils } from "@web_tour/tour_utils";

const tours = registry.category("web_tour.tours");

// The slot tests start at the event page with the ids of the slots in the URL's
// fragment, which survives the event page's redirects: `#soon=<id>&later=<id>`.
const params = () => new URLSearchParams(window.location.hash.slice(1));

const REGISTER = ".btn-primary:contains(Register):visible";
const MODAL = "#modal_slot_registration";
const slotButton = (id) => `${MODAL} .o_wevent_slot_btn[data-slot-id="${id}"]`;

// Core's notice for an event nobody can register for any more.
tours.add("vmk_event_registration_deadline_closed", {
    steps: () => [
        {
            content: "the page says registrations are closed",
            trigger: ".alert-warning:contains(Closed)",
        },
        {
            content: "and offers no way to register",
            trigger: `body:not(:has(${REGISTER}))`,
        },
    ],
});

tours.add("vmk_event_registration_deadline_open", {
    steps: () => [
        {
            content: "the page offers to register",
            trigger: REGISTER,
        },
        {
            content: "and does not say registrations are closed",
            trigger: "body:not(:has(.alert-warning:contains(Closed)))",
        },
    ],
});

const openModal = () => [
    {
        content: "open the registration pop-up",
        trigger: REGISTER,
        run: "click",
    },
];

tours.add("vmk_event_registration_deadline_slots", {
    steps: () => [
        ...openModal(),
        {
            content: "the later slot is offered",
            trigger: slotButton(params().get("later")),
        },
        {
            content: "the slot inside the deadline is not",
            trigger: `${MODAL}:not(:has(.o_wevent_slot_btn[data-slot-id="${params().get("soon")}"]))`,
        },
    ],
});

tours.add("vmk_event_registration_deadline_slots_offered", {
    steps: () => [
        ...openModal(),
        {
            content: "the later slot is offered",
            trigger: slotButton(params().get("later")),
        },
        {
            content: "and so is the sooner one",
            trigger: slotButton(params().get("soon")),
        },
    ],
});

tours.add("vmk_event_registration_deadline_settings", {
    steps: () => [
        {
            content: "the time field is hidden while the switch is off",
            trigger: `.o_field_widget[name="vmk_registration_deadline_enabled"] input:not(:checked)`,
        },
        {
            content: "the time before start is not shown",
            trigger: `body:not(:has(.o_field_widget[name="vmk_registration_deadline_hours"]:visible))`,
        },
        {
            content: "turn the deadline on",
            trigger: `.o_field_widget[name="vmk_registration_deadline_enabled"] input`,
            run: "click",
        },
        {
            content: "set the time before the start",
            trigger: `.o_field_widget[name="vmk_registration_deadline_hours"] input`,
            run: "edit 3h 30m",
        },
        {
            // Settings reload the whole client once saved.
            content: "save, and let the page reload",
            trigger: ".o_form_button_save:enabled",
            expectUnloadPage: true,
            run: "click",
        },
        {
            content: "the saved setting is shown after the reload",
            trigger: `.o_field_widget[name="vmk_registration_deadline_hours"] input:value("3h 30m")`,
        },
    ],
});

tours.add("vmk_event_registration_deadline_event_form", {
    steps: () => [
        {
            content: "the time field is hidden until the event asks for a deadline",
            trigger: `.o_field_widget[name="vmk_deadline_custom"] input:not(:checked)`,
        },
        {
            content: "no time before start is shown yet",
            trigger: `body:not(:has(.o_field_widget[name="vmk_deadline_hours"]:visible))`,
        },
        {
            content: "tick the event's own deadline",
            trigger: `.o_field_widget[name="vmk_deadline_custom"] input`,
            run: "click",
        },
        {
            content: "set an hour before the start",
            trigger: `.o_field_widget[name="vmk_deadline_hours"] input`,
            run: "edit 1h",
        },
        ...stepUtils.saveForm(),
        {
            content: "the saved deadline is shown",
            trigger: `.o_field_widget[name="vmk_deadline_hours"] input:value("1h")`,
        },
    ],
});
