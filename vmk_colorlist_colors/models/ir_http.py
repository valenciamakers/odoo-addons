# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import models


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    def session_info(self):
        """The twelve colors' names, in the user's language, for the color
        pickers (static/src/colorlist.js), keyed by slot. All twelve, not
        only the renamed ones, so the pickers show the names the list shows,
        including where our catalogue translates a name core leaves in
        English."""
        info = super().session_info()
        colors = self.env["vmk.colorlist.color"].sudo().with_context(lang=self.env.lang).search([])
        info["vmk_colorlist_names"] = {color.slot: color.name for color in colors}
        return info
