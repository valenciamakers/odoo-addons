# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import fields, models


class EventEvent(models.Model):
    _inherit = "event.event"

    # Contacts rather than users: a host is often an outside speaker or a
    # freelance teacher with no login, and Organizer is already the company
    # putting the event on rather than the person running it.
    vmk_host_ids = fields.Many2many(
        "res.partner",
        "vmk_event_host_rel",
        "event_id",
        "partner_id",
        string="Hosts",
        tracking=True,
        help="The people running the event: speakers, teachers or facilitators.",
    )
