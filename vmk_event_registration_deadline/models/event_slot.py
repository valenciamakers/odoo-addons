# Copyright 2026 Valencia Makers, SL
# License AGPL-3 (https://www.gnu.org/licenses/agpl-3.0.html).

from datetime import datetime, timedelta

from odoo import models


class EventSlot(models.Model):
    _inherit = "event.slot"

    def _filter_open_slots(self):
        """Retire a slot the deadline has reached, not merely one that started.

        Core already drops a slot whose `start_datetime` has passed
        (`website_event/models/event_slot.py`), so the start itself is covered.
        What it has no notion of is a lead time, and without this the policy
        would apply to single events and not to slots — sales stopping two
        hours early for one and exactly on the hour for the other.

        Only ever tightens core's filter. A ticket's own Registration End
        overrides the rule on a single event, but not here: it cannot loosen a
        deadline core itself applies, and on a multi-slot event a ticket says
        nothing about which slot it belongs to.
        """
        slots = super()._filter_open_slots()
        if not slots:
            return slots
        now = datetime.now()

        def still_open(slot):
            deadline = slot.event_id._vmk_deadline_hours()
            if deadline is None:
                return True
            return slot.start_datetime - timedelta(hours=deadline) > now

        return slots.filtered(still_open)
