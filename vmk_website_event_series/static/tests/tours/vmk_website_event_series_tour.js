// Copyright 2026 Valencia Makers, SL
// License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

import { registry } from "@web/core/registry";

const tours = registry.category("web_tour.tours");

// The /event listing's Series filter narrows the list to one series, and
// the event's page links back to the series' own page.
tours.add("vmk_website_event_series_filter_tour", {
    steps: () => [
        {
            content: "both events are listed",
            trigger: `.o_wevent_events_list:contains("VMK Tour Date"):contains("VMK Tour Other")`,
        },
        {
            content: "open the Series filter",
            trigger: `.o_vmk_event_series_filter button.dropdown-toggle:contains("All Series")`,
            run: "click",
        },
        {
            content: "choose the series",
            trigger: `.o_vmk_event_series_filter .dropdown-menu a:contains("VMK Tour Series")`,
            run: "click",
            expectUnloadPage: true,
        },
        {
            content: "only its event is listed",
            trigger: `.o_wevent_events_list:contains("VMK Tour Date"):not(:contains("VMK Tour Other"))`,
        },
        {
            content: "and the filter names it",
            trigger: `.o_vmk_event_series_filter button.dropdown-toggle:contains("VMK Tour Series")`,
        },
        {
            content: "open the event",
            trigger: `.o_wevent_events_list a:contains("VMK Tour Date")`,
            run: "click",
            expectUnloadPage: true,
        },
        {
            content: "its page links to the series",
            trigger: `.o_vmk_event_series_link a:contains("VMK Tour Series")`,
            run: "click",
            expectUnloadPage: true,
        },
        {
            content: "the series' page lists the date",
            trigger: `.o_vmk_event_series_dates:contains("VMK Tour Date")`,
        },
    ],
});
