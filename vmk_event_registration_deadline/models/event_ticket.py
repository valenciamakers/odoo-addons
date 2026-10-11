# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from datetime import timedelta

from odoo import api, fields, models


class EventEventTicket(models.Model):
    _inherit = "event.event.ticket"

    @api.depends(
        "end_sale_datetime",
        "event_id.date_begin",
        "event_id.is_multi_slots",
        "event_id.vmk_deadline_custom",
        "event_id.vmk_deadline_hours",
    )
    def _compute_is_expired(self):
        """Expire a ticket that has no Registration End at the event's deadline.

        Core expires a ticket by its own `end_sale_datetime` alone, and keeps
        one without a date on sale until the event ends. Here the deadline
        stands in for the missing date: a ticket that says nothing closes a
        set time before the event starts, and a ticket with a typed
        Registration End keeps it, whether that is earlier or later than the
        deadline. An Early Bird ticket that ends a month early therefore
        expires by its own date while the Regular ticket beside it still
        closes at the deadline; a ticket deliberately ending at the start
        keeps selling past it.

        Everything downstream then follows core with no code of ours:
        `sale_available`, the event's own `event_registrations_open`, which
        closes once no ticket is on sale, the website page, which lists the
        ticket as Expired, and `website_event`'s confirm step, which refuses
        an expired ticket, so a form opened before the deadline cannot be
        submitted after it.

        Multi-slot events are left alone: the deadline is per slot there
        (`event_slot.py`), and a ticket says nothing about which slot it is
        sold for.
        """
        super()._compute_is_expired()
        now = fields.Datetime.now()
        for ticket in self:
            event = ticket.event_id
            if (
                ticket.is_expired
                or ticket.end_sale_datetime
                or event.is_multi_slots
                or not event.date_begin
            ):
                continue
            deadline = event._vmk_deadline_hours()
            if deadline is not None and event.date_begin - timedelta(hours=deadline) <= now:
                ticket.is_expired = True
