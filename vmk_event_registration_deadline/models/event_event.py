# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from .res_config_settings import DEADLINE_PARAM, ENABLED_PARAM


class EventEvent(models.Model):
    _inherit = "event.event"

    # A boolean beside the value, the way core pairs `seats_limited` with
    # `seats_max`. A float alone could not say "no override": zero is a real
    # setting, meaning close exactly as the event begins.
    vmk_deadline_custom = fields.Boolean(
        string="Registration Deadline",
        help="Use a custom registration deadline for the event, overriding the "
        "global setting.",
    )
    # No `help`: the field renders inline beside the checkbox with no label of
    # its own, and Odoo hangs the `?` off a label, so anything here is never
    # seen. "Before Start" sits next to the value and says it anyway.
    vmk_deadline_hours = fields.Float(string="Time Before Start")

    @api.constrains("vmk_deadline_hours")
    def _check_vmk_deadline_hours(self):
        """Refuse a negative time: it would close registration after the start."""
        if any(event.vmk_deadline_hours < 0 for event in self):
            raise ValidationError(_("The time before start cannot be negative."))

    def _vmk_deadline_hours(self):
        """This event's deadline in hours, or None where none applies.

        An event that sets its own is opted in whatever the global switch
        says: the switch means "apply a deadline to events by default", and an
        event asking for one has already answered for itself. Turning the
        feature off therefore stops it applying everywhere it was implicit,
        and nowhere it was asked for.
        """
        self.ensure_one()
        if self.vmk_deadline_custom:
            return self.vmk_deadline_hours
        config = self.env["ir.config_parameter"].sudo()
        if config.get_param(ENABLED_PARAM) not in ("True", "true", "1"):
            return None
        return float(config.get_param(DEADLINE_PARAM) or 0.0)

    @api.depends(
        "date_begin",
        "vmk_deadline_custom",
        "vmk_deadline_hours",
        "event_slot_ids.start_datetime",
    )
    def _compute_event_registrations_open(self):
        """Close registration once the event has started, or is about to.

        Core has no notion of a start deadline: `event_registrations_open`
        checks `date_end` and nothing else about the event's own dates, so a
        one-day workshop is still on sale minutes before it finishes. This
        adds the rule rather than replacing anything — core decides first, and
        this can only ever close what core left open.

        One case is judged by its tickets, and one by its slots:

        * **An event with tickets.** Each ticket without a Registration End
          takes the deadline as its own expiry (`event_ticket.py`), and one
          with a typed end keeps it. Core's own compute then closes the event
          once no ticket is on sale, so nothing is decided here. Until
          19.0.1.3.0 this rule exempted the whole event when any ticket had an
          end date, which let an Early Bird ticket's early end keep the Regular
          ticket beside it selling into the event start.
        * **Multi-slot events.** Their `date_begin` is the earliest slot's
          start, so closing the event there would stop selling every later
          slot too. Core handles those per slot, and so does this module —
          see `event_slot.py`. The event closes only once the deadline has
          reached every one of its slots: until then a later slot is still on
          sale, and after that the page would offer Register over a pop-up
          with no dates in it. Core leaves that gap open from the last slot's
          start to the event's end; a deadline widens it by its own length.
        """
        super()._compute_event_registrations_open()
        now = fields.Datetime.now()
        for event in self:
            if not event.event_registrations_open:
                continue
            deadline = event._vmk_deadline_hours()
            if deadline is None:
                continue
            lead = timedelta(hours=deadline)
            if event.is_multi_slots:
                # An event with no slots yet is left as core has it.
                starts = event.event_slot_ids.mapped("start_datetime")
                if starts and all(start - lead <= now for start in starts):
                    event.event_registrations_open = False
                continue
            if event.event_ticket_ids:
                continue
            if event.date_begin and event.date_begin - lead <= now:
                event.event_registrations_open = False
