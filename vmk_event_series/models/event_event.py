# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import fields, models


class EventEvent(models.Model):
    _inherit = "event.event"

    # A plain link: unlike the template beside it on the form, choosing a
    # series fills nothing in. A series with events cannot be deleted, only
    # archived, so no event is left pointing at nothing.
    series_id = fields.Many2one(
        "vmk.event.series",
        string="Series",
        index="btree_not_null",
        ondelete="restrict",
    )
