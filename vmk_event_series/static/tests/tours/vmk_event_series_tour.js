// Copyright 2026 Valencia Makers, SL
// License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

import { registry } from "@web/core/registry";
import { stepUtils } from "@web_tour/tour_utils";

const tours = registry.category("web_tour.tours");

// From a series, New Event in Series opens an event already in the series,
// named after it and on its template.
tours.add("vmk_event_series_new_event_tour", {
    steps: () => [
        {
            content: "the series counts its upcoming events",
            trigger: `.o_form_view button[name="action_view_events"]:contains("Upcoming Events") .o_stat_value:contains("1")`,
        },
        {
            content: "add an event",
            trigger: `.o_form_view button[name="action_new_event"]:contains("New Event in Series")`,
            run: "click",
        },
        {
            content: "the new event is in the series",
            trigger: `.o_form_view .o_field_widget[name="series_id"] input:value("Tour Series")`,
        },
        {
            content: "on its template",
            trigger: `.o_form_view .o_field_widget[name="event_type_id"] input:value("Tour Template")`,
        },
        {
            content: "and named after it",
            trigger: `.o_form_view .o_field_widget[name="name"] textarea:value("Tour Series"), .o_form_view .o_field_widget[name="name"] input:value("Tour Series")`,
        },
        ...stepUtils.discardForm(),
    ],
});
