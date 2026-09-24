# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from datetime import datetime, timedelta

import pytz

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.date_utils import float_to_time
from odoo.tools.misc import format_date, format_time


class EventSlot(models.Model):
    _inherit = "event.slot"

    # Core's slot is one `date` and two hours on it. What this module adds is
    # how many days later it ends, stored as a count rather than a date: a
    # slot's length is then part of the slot, so moving its date by any route
    # -- the form, an import, core's own code writing `date` -- moves its end
    # with it, and a slot within one day stays within one day.
    vmk_end_day_offset = fields.Integer(
        string="Days Spanned",
        default=0,
        help="How many days after its date the slot ends. 0 for a slot within one day.",
    )
    # Readable and writable for convenience; `create` and `write` turn it
    # into the day count before anything is stored or checked.
    vmk_end_date = fields.Date(
        string="End Date",
        compute="_compute_vmk_end_date",
        store=True,
        readonly=False,
        help="The day the slot ends. The same as its date for a slot within one day.",
    )

    @api.depends("date", "vmk_end_day_offset")
    def _compute_vmk_end_date(self):
        for slot in self:
            slot.vmk_end_date = slot.date and slot.date + timedelta(days=slot.vmk_end_day_offset)

    def _vmk_is_multiday(self):
        self.ensure_one()
        return self.vmk_end_day_offset > 0

    @api.model
    def _vmk_end_date_to_offset(self, vals, date):
        """Replace an end date in `vals` with the day count from `date`.

        Done up front rather than in an inverse: Odoo checks the other
        fields of a write before it runs an inverse, so a new end hour
        would meet core's one-day hour check while the slot was still one
        day long. Given both, the day count wins, so the two cannot be
        stored disagreeing.
        """
        end = fields.Date.to_date(vals.pop("vmk_end_date"))
        date = fields.Date.to_date(date)
        if "vmk_end_day_offset" not in vals:
            vals["vmk_end_day_offset"] = (end - date).days if end and date else 0
        return vals

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if "vmk_end_date" in vals:
                self._vmk_end_date_to_offset(vals, vals.get("date"))
        return super().create(vals_list)

    def write(self, vals):
        if "vmk_end_date" not in vals:
            return super().write(vals)
        if "date" in vals:
            return super().write(self._vmk_end_date_to_offset(dict(vals), vals["date"]))
        # Each slot's count runs from its own date.
        for slot in self:
            super(EventSlot, slot).write(slot._vmk_end_date_to_offset(dict(vals), slot.date))
        return True

    @api.depends("vmk_end_day_offset")
    def _compute_datetimes(self):
        """End a multi-day slot on its own end date.

        Core computes both ends on `date`. Everything core then reads from
        `end_datetime` -- the registration's end date, the "after the event
        ended" mail, the calendar, the calendar file, its check that the slot
        fits inside its event -- follows the real end without any change of
        its own.

        A slot not yet given a date, or an event to take a timezone from,
        has no datetimes. Core's compute would fail on it, and never meets
        one because core's form does not show the datetimes; ours does.
        """
        incomplete = self.filtered(lambda slot: not (slot.date and slot.date_tz))
        incomplete.start_datetime = incomplete.end_datetime = False
        complete = self - incomplete
        super(EventSlot, complete)._compute_datetimes()
        for slot in complete.filtered(lambda slot: slot._vmk_is_multiday()):
            timezone = pytz.timezone(slot.date_tz)
            local_end = datetime.combine(slot.vmk_end_date, float_to_time(slot.end_hour))
            slot.end_datetime = (
                timezone.localize(local_end).astimezone(pytz.UTC).replace(tzinfo=None)
            )

    @api.constrains("start_hour", "end_hour", "vmk_end_day_offset")
    def _check_hours(self):
        """Core's hour check for a one-day slot; the real order for the rest.

        Core requires the end hour to be later than the start hour, which is
        what "ends after it starts" means within one day. Across days it is
        not: a slot from Friday 18:00 to Sunday 13:00 is valid. So core's
        own check runs for one-day slots, and a multi-day one only needs its
        hours to be hours; its end is already later, being on a later day.
        """
        self._check_vmk_end_day_offset()
        one_day = self.filtered(lambda slot: not slot._vmk_is_multiday())
        super(EventSlot, one_day)._check_hours()
        for slot in self - one_day:
            if not (0 <= slot.start_hour <= 23.99 and 0 <= slot.end_hour <= 23.99):
                raise ValidationError(_("A slot hour must be between 0:00 and 23:59."))

    @api.constrains("vmk_end_day_offset")
    def _check_vmk_end_day_offset(self):
        for slot in self:
            if slot.vmk_end_day_offset < 0:
                raise ValidationError(
                    _(
                        "A slot cannot end before it starts: %(slot)s ends on %(end)s.",
                        slot=slot.display_name,
                        end=format_date(self.env, slot.vmk_end_date),
                    )
                )

    @api.depends("date", "start_hour", "end_hour", "vmk_end_day_offset")
    def _compute_display_name(self):
        """Name a multi-day slot by both its days.

        Core names a slot "Oct 9, 2026, 18:00 - 20:00", its date and its hour
        range, which on a slot that ends another day would read as one
        evening. A multi-day slot reads "Oct 9, 2026, 18:00 - Oct 11, 2026,
        13:00" instead, in the same formats core uses.
        """
        super()._compute_display_name()
        for slot in self.filtered(lambda slot: slot._vmk_is_multiday()):
            slot.display_name = "%s, %s - %s, %s" % (
                format_date(self.env, slot.date, date_format="medium"),
                format_time(self.env, float_to_time(slot.start_hour), time_format="short"),
                format_date(self.env, slot.vmk_end_date, date_format="medium"),
                format_time(self.env, float_to_time(slot.end_hour), time_format="short"),
            )
