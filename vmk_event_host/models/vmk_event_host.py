# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import api, fields, models


class VmkEventHost(models.Model):
    _name = "vmk.event.host"
    _description = "Event Host"
    # A line model exists here only to give hosts an order. A many2many has no
    # column to hold a position, so its records come back in the target model's
    # own order -- for contacts, alphabetically by complete_name.
    _order = "event_id, sequence, id"

    event_id = fields.Many2one(
        "event.event",
        string="Event",
        required=True,
        ondelete="cascade",
        index=True,
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Host",
        required=True,
        index=True,
        help="The person running the event: a speaker, teacher or facilitator.",
    )
    role = fields.Char(
        string="Role",
        help="What this host does, when it is worth saying: Lead, Assistant, Guest speaker.",
    )
    sequence = fields.Integer(default=10)
    company_id = fields.Many2one(
        related="event_id.company_id",
        store=True,
        index=True,
    )

    _partner_event_uniq = models.Constraint(
        "unique(event_id, partner_id)",
        "A contact can only be listed once as a host of an event.",
    )

    @api.depends("partner_id", "role")
    def _compute_display_name(self):
        for host in self:
            name = host.partner_id.display_name or ""
            host.display_name = f"{name} ({host.role})" if host.role else name
