// Copyright 2026 Valencia Makers, SL
// License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

import { Component, xml } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { DateTimeField, dateRangeField } from "@web/views/fields/datetime/datetime_field";

/**
 * A slot's start and end as one range, the way the event form shows its
 * dates, in the event's timezone.
 *
 * Core stores a slot as a date and two hours in the event's timezone, and
 * shows it in that timezone everywhere: the hours on its form, the slot
 * calendar, its name. A datetime field would show the viewer's own time and
 * disagree with all three for anyone editing from another timezone.
 *
 * So this does what core's slot calendar does
 * (`event/static/src/views/event_slot_calendar/event_slot_calendar_model.js`):
 * - to show a slot, `normalizeRecord` converts its datetimes to the event's
 *   zone and relabels them local, keeping the wall-clock time;
 * - to save one, `buildRawRecord` writes `date`, `start_hour` and `end_hour`
 *   from that wall-clock time, never the datetimes.
 *
 * Core's `DateTimeField` does the rest unchanged. It is handed a view of the
 * record in which the range reads as event time, and in which updating the
 * range writes the slot's own fields instead, plus this module's day count.
 */
const toEventTime = (value, tz) =>
    value ? value.setZone(tz).setZone("local", { keepLocalTime: true }) : value;
const hourOf = (value) => value.hour + value.minute / 60;

// Written by this widget, so they must be loaded and saved, and must call the
// server's onchange: that is what recomputes the datetimes the range shows.
// The server marks a field for onchange only where the view's arch declares
// it; `vmk_event_sessions` happens to declare `date`, which hid this, and on
// a database without it an edit left the range showing the old dates.
const SLOT_FIELDS = [
    { name: "date", type: "date" },
    { name: "start_hour", type: "float" },
    { name: "end_hour", type: "float" },
    { name: "vmk_end_day_offset", type: "integer" },
];

export class EventSlotDateRangeField extends Component {
    static template = xml`<DateTimeField t-props="dateTimeFieldProps"/>`;
    static components = { DateTimeField };
    static props = { ...DateTimeField.props, tzField: String };

    get dateTimeFieldProps() {
        const { tzField, ...props } = this.props;
        const record = this.props.record;
        const tz = record.data[tzField] || "UTC";
        const [startName, endName] = [props.startDateField || props.name, props.endDateField];
        const data = new Proxy(record.data, {
            get: (target, key) =>
                key === startName || key === endName ? toEventTime(target[key], tz) : target[key],
        });
        const update = (changes, options) => {
            const start = changes[startName] || data[startName];
            const end = changes[endName] || data[endName];
            if (!start || !end) {
                return;
            }
            const [startDay, endDay] = [start.startOf("day"), end.startOf("day")];
            return record.update(
                {
                    date: startDay,
                    start_hour: hourOf(start),
                    end_hour: hourOf(end),
                    vmk_end_day_offset: Math.round(endDay.diff(startDay, "days").days),
                },
                options
            );
        };
        return {
            ...props,
            record: new Proxy(record, {
                get: (target, key) => {
                    if (key === "data") {
                        return data;
                    }
                    if (key === "update") {
                        return update;
                    }
                    const value = target[key];
                    return typeof value === "function" ? value.bind(target) : value;
                },
            }),
        };
    }
}

export const eventSlotDateRangeField = {
    ...dateRangeField,
    component: EventSlotDateRangeField,
    displayName: _t("Slot Date Range"),
    supportedTypes: ["datetime"],
    extractProps: (fieldInfo, dynamicInfo) => ({
        ...dateRangeField.extractProps(fieldInfo, dynamicInfo),
        tzField: fieldInfo.options.tz_field || "date_tz",
    }),
    fieldDependencies: (fieldInfo) => [
        ...dateRangeField.fieldDependencies(fieldInfo),
        ...SLOT_FIELDS.map((field) => ({ ...field, readonly: false, onChange: true })),
    ],
};

registry.category("fields").add("vmk_event_slot_daterange", eventSlotDateRangeField);
