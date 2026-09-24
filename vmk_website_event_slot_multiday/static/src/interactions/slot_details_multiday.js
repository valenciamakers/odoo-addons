// Copyright 2026 Valencia Makers, SL
// License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

import { deserializeDateTime } from "@web/core/l10n/dates";
import { patch } from "@web/core/utils/patch";
import { SlotDetails } from "@website_event/interactions/website_event_slot_details";

const { DateTime } = luxon;

/**
 * Print both days of a multi-day slot in the registration modal.
 *
 * Core's "Selected Date" line prints the chosen slot's start as a date and
 * time and its end as a time alone (`website_event_slot_details.js`,
 * `_onSlotSelected`), since a core slot never leaves its day. A slot from
 * Friday 18:00 to Sunday 13:00 would read "Fri, Oct 9, 2026, 6:00 PM -
 * 1:00 PM", which says one evening. Where the slot ends on another day, its
 * end gets a date too; a one-day slot keeps core's line exactly.
 */
patch(SlotDetails.prototype, {
    _onSlotSelected(ev) {
        super._onSlotSelected(ev);
        const { slotStart, slotEnd, eventTz } = ev.currentTarget.dataset;
        const start = deserializeDateTime(slotStart, { tz: eventTz });
        const end = deserializeDateTime(slotEnd, { tz: eventTz });
        if (!start.hasSame(end, "day")) {
            this.selectedSlotDatetime =
                start.toLocaleString(DateTime.DATETIME_MED_WITH_WEEKDAY) +
                " - " +
                end.toLocaleString(DateTime.DATETIME_MED_WITH_WEEKDAY);
        }
    },
});
