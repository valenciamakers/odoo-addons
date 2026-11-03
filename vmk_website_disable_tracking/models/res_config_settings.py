# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    website_vmk_track_visitors = fields.Boolean(
        related="website_id.vmk_track_visitors",
        readonly=False,
    )
