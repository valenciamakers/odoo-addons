# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from datetime import datetime

import pytz

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.date_utils import float_to_time
from odoo.tools.misc import format_date, format_time


class EventSlot(models.Model):
    _inherit = "event.slot"

    # Core's slot is one `date` and two hours on it. This is the day it ends,
    # so a slot can run from Friday evening to Sunday afternoon. Stored and
    # computed so every slot has one, the same day as `date` unless set: an
    # existing slot is a one-day slot on install, exactly as before.
    vmk_end_date = fields.Date(
        string="End Date",
        compute="_compute_vmk_end_date",
        store=True,
        readonly=False,
        precompute=True,
        help="The day the slot ends. The same as its date for a slot within one day.",
    )

    @api.depends("date")
    def _compute_vmk_end_date(self):
        """The slot's own date, until an end date is given or it falls behind.

        Only fills a missing end, or one that `date` has moved past: a later
        end already set is kept, which is what makes a slot multi-day.
        Moving a whole multi-day slot is handled in `write`, which knows by
        how much it moved.
        """
        for slot in self:
            if not slot.vmk_end_date or (slot.date and slot.vmk_end_date < slot.date):
                slot.vmk_end_date = slot.date

    def _vmk_is_multiday(self):
        self.ensure_one()
        return bool(self.date and self.vmk_end_date and self.vmk_end_date > self.date)

    @api.depends("vmk_end_date")
    def _compute_datetimes(self):
        """End a multi-day slot on its own end date.

        Core computes both ends on `date`. Everything core then reads from
        `end_datetime` -- the registration's end date, the "after the event
        ended" mail, the calendar, the calendar file, its check that the slot
        fits inside its event -- follows the real end without any change of
        its own.
        """
        super()._compute_datetimes()
        for slot in self.filtered(lambda slot: slot._vmk_is_multiday()):
            timezone = pytz.timezone(slot.date_tz or "UTC")
            local_end = datetime.combine(slot.vmk_end_date, float_to_time(slot.end_hour))
            slot.end_datetime = (
                timezone.localize(local_end).astimezone(pytz.UTC).replace(tzinfo=None)
            )

    @api.constrains("start_hour", "end_hour", "vmk_end_date")
    def _check_hours(self):
        """Core's hour check for a one-day slot; the real order for the rest.

        Core requires the end hour to be later than the start hour, which is
        what "ends after it starts" means within one day. Across days it is
        not: a slot from Friday 18:00 to Sunday 13:00 is valid. So core's
        own check runs for one-day slots, and a multi-day one only needs its
        hours to be hours; its end is already later, being on a later day.
        """
        one_day = self.filtered(lambda slot: not slot._vmk_is_multiday())
        super(EventSlot, one_day)._check_hours()
        for slot in self - one_day:
            if not (0 <= slot.start_hour <= 23.99 and 0 <= slot.end_hour <= 23.99):
                raise ValidationError(_("A slot hour must be between 0:00 and 23:59."))

    @api.constrains("date", "vmk_end_date")
    def _check_vmk_end_date(self):
        for slot in self:
            if slot.date and slot.vmk_end_date and slot.vmk_end_date < slot.date:
                raise ValidationError(
                    _(
                        "A slot cannot end before it starts: %(slot)s ends on %(end)s.",
                        slot=slot.display_name,
                        end=format_date(self.env, slot.vmk_end_date),
                    )
                )

    def write(self, vals):
        """Keep a multi-day slot's length when only its start date moves.

        Moving a one-day slot to another day keeps its hours. The same move
        for a Friday-to-Sunday slot should keep it Friday to Sunday, not
        stretch or collapse it, so the end moves by as many days as the
        start did. Writing both dates at once is taken as written.
        """
        if "date" in vals and "vmk_end_date" not in vals:
            new_date = fields.Date.to_date(vals["date"])
            multiday = self.filtered(lambda slot: slot._vmk_is_multiday())
            for slot in multiday:
                length = slot.vmk_end_date - slot.date
                super(EventSlot, slot).write(dict(vals, vmk_end_date=new_date + length))
            if multiday:
                rest = self - multiday
                return super(EventSlot, rest).write(vals) if rest else True
        return super().write(vals)

    @api.depends("vmk_end_date")
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
