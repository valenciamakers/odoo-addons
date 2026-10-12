# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import api, fields, models
from odoo.exceptions import ValidationError


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

    # There is deliberately no SQL unique constraint on (event_id, partner_id).
    # base/wizard/base_partner_merge.py re-points every foreign key to res_partner
    # in raw SQL, this table's with one bulk UPDATE in a savepoint whose error
    # handler falls back to
    # `DELETE FROM vmk_event_host WHERE partner_id IN <every source id>`. A unique
    # constraint made that UPDATE fail on the collision two co-hosts produce, and
    # the merged contacts then lost every host line they had, on every event.
    # Uniqueness lives in _check_partner_unique, which that raw SQL bypasses
    # anyway; _vmk_dedupe removes the duplicate it can leave behind.

    @api.constrains("event_id", "partner_id")
    def _check_partner_unique(self):
        for host in self:
            duplicate = self.search(
                [
                    ("event_id", "=", host.event_id.id),
                    ("partner_id", "=", host.partner_id.id),
                    ("id", "!=", host.id),
                ],
                limit=1,
            )
            if duplicate:
                raise ValidationError(
                    self.env._("A contact can only be listed once as a host of an event.")
                )

    @api.model
    def _vmk_dedupe(self, partner, keep=()):
        """Keep one line per event for ``partner``, after a contact merge.

        The merge wizard re-points the merged contacts' lines with one bulk
        ``UPDATE`` that compares no values and bypasses ``_check_partner_unique``,
        so an event two merged contacts both hosted holds the survivor twice.
        ``keep`` names the lines that were the survivor's own before the merge:
        on a shared event that one stays, with its role and position, and the
        merged contact's goes. Where none of an event's lines is named, the one
        that sorts first (lowest sequence, then oldest) stays. Every event the
        survivor hosts then recomputes its mirror and summary, since the raw SQL
        told the cache nothing.
        """
        self.invalidate_model()
        lines = self.search([("partner_id", "=", partner.id)])  # in _order
        events = lines.event_id
        keep = set(keep)
        extra = self.browse()
        for event_lines in lines.grouped("event_id").values():
            if len(event_lines) < 2:
                continue
            kept = event_lines.filtered(lambda line: line.id in keep)[:1] or event_lines[:1]
            extra |= event_lines - kept
        if extra:
            extra.unlink()
        events.invalidate_recordset(["vmk_host_ids"])
        events.modified(["vmk_host_ids"])

    @api.depends("partner_id", "role")
    def _compute_display_name(self):
        for host in self:
            name = host.partner_id.display_name or ""
            host.display_name = f"{name} ({host.role})" if host.role else name
