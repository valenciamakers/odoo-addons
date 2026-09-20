# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import api, fields, models


class EventEvent(models.Model):
    _inherit = "event.event"

    # Contacts rather than users: a host is often an outside speaker or a
    # freelance teacher with no login, and Organizer is already the company
    # putting the event on rather than the person running it.
    vmk_host_ids = fields.One2many(
        "vmk.event.host",
        "event_id",
        string="Host Lines",
        copy=True,
    )
    # The form header shows this rather than the mirror below, because a
    # many2many renders in the target model's order -- so the summary would
    # contradict the order set in the Hosts tab, which is the whole point of
    # the line model.
    vmk_host_names = fields.Char(
        string="Hosts",
        compute="_compute_vmk_host_names",
    )
    # Ordering is why the line model exists, and it costs the search view its
    # field: neither grouping nor an `in` domain works on a one2many. This
    # mirror carries both, and a stored compute keeps it usable in a domain.
    vmk_host_partner_ids = fields.Many2many(
        "res.partner",
        "vmk_event_host_partner_rel",
        "event_id",
        "partner_id",
        string="Hosts",
        compute="_compute_vmk_host_partner_ids",
        store=True,
        tracking=True,
    )

    @api.depends("vmk_host_ids.partner_id")
    def _compute_vmk_host_partner_ids(self):
        for event in self:
            event.vmk_host_partner_ids = event.vmk_host_ids.partner_id

    @api.depends("vmk_host_ids.partner_id", "vmk_host_ids.sequence")
    def _compute_vmk_host_names(self):
        for event in self:
            # Sorted explicitly: a one2many keeps the order it was read in
            # until the cache is invalidated, so writing `sequence` alone
            # leaves `vmk_host_ids` in its old order within the same
            # transaction -- and the summary would lag a drag-and-drop.
            hosts = event.vmk_host_ids.sorted(lambda host: (host.sequence, host.id))
            event.vmk_host_names = ", ".join(host.display_name for host in hosts)
