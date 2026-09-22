# Copyright 2026 Valencia Makers, SL
# License AGPL-3 (https://www.gnu.org/licenses/agpl-3.0.html).

from datetime import timedelta

from odoo import api, fields, models

from .res_config_settings import CUTOFF_PARAM, ENABLED_PARAM


class EventEvent(models.Model):
    _inherit = "event.event"

    # A boolean beside the value, the way core pairs `seats_limited` with
    # `seats_max`. A float alone could not say "no override": zero is a real
    # setting, meaning close exactly as the event begins.
    vmk_cutoff_custom = fields.Boolean(
        string="Custom Registration Cutoff",
        help="Use a cutoff for this event instead of the one in Settings.",
    )
    vmk_cutoff_hours = fields.Float(
        string="Close Registration Before Start",
        help="How long before this event starts registration closes.",
    )

    def _vmk_cutoff_hours(self):
        """This event's cutoff in hours, or None where none applies.

        An event that sets its own is opted in whatever the global switch
        says: the switch means "apply a cutoff to events by default", and an
        event asking for one has already answered for itself. Turning the
        feature off therefore stops it applying everywhere it was implicit,
        and nowhere it was asked for.
        """
        self.ensure_one()
        if self.vmk_cutoff_custom:
            return self.vmk_cutoff_hours
        config = self.env["ir.config_parameter"].sudo()
        if config.get_param(ENABLED_PARAM) not in ("True", "true", "1"):
            return None
        return float(config.get_param(CUTOFF_PARAM) or 0.0)

    @api.depends("date_begin", "vmk_cutoff_custom", "vmk_cutoff_hours")
    def _compute_event_registrations_open(self):
        """Close registration once the event has started, or is about to.

        Core has no notion of a start cutoff: `event_registrations_open`
        checks `date_end` and nothing else about the event's own dates, so a
        one-day workshop is still on sale minutes before it finishes. This
        adds the rule rather than replacing anything — core decides first, and
        this can only ever close what core left open.

        Two cases are deliberately left alone:

        * **A ticket with its own Registration End.** Core's `is_expired` is
          False whenever `end_sale_datetime` is blank, so blank is what this
          rule is for; a date somebody typed is a deliberate choice to allow
          late registration, and it wins.
        * **Multi-slot events.** Their `date_begin` is the earliest slot's
          start, so closing the event there would stop selling every later
          slot too. Core handles those per slot, and so does this module —
          see `event_slot.py`.
        """
        super()._compute_event_registrations_open()
        now = fields.Datetime.now()
        for event in self:
            if not event.event_registrations_open or event.is_multi_slots:
                continue
            if any(ticket.end_sale_datetime for ticket in event.event_ticket_ids):
                continue
            cutoff = event._vmk_cutoff_hours()
            if cutoff is None or not event.date_begin:
                continue
            if event.date_begin - timedelta(hours=cutoff) <= now:
                event.event_registrations_open = False
