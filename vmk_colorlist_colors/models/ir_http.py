# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import models


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    def session_info(self):
        """The renamed colors, in the user's language, for the color pickers
        (static/src/colorlist.js), keyed by slot. Only the renamed ones: the
        others keep Odoo's names and Odoo's translations of them."""
        info = super().session_info()
        names = {
            color.slot: color.name
            for color in self.env["vmk.colorlist.color"].sudo().with_context(
                lang=self.env.lang
            ).search([("name", "!=", False)])
        }
        if names:
            info["vmk_colorlist_names"] = names
        return info
