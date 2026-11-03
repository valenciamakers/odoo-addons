# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import fields, models


class Website(models.Model):
    _inherit = "website"

    vmk_track_visitors = fields.Boolean(
        string="Track Visitors",
        default=False,
        help="Record each visitor and the pages they view, under Website › Reporting › Visitors. "
        "Off, the website records no visitors at all.",
    )

    def _is_tracking_enabled(self, main_object):
        """Whether the page asks the browser to report the view.

        Website marks the page `data-tracking-enabled`, and its tracker then
        calls `/website/odoo_track`, which records the visitor and the page.
        Off, the page carries no mark, so the browser never calls. The route
        itself is closed in `ir.http`, for a call made by hand.
        """
        if not self.vmk_track_visitors:
            return False
        return super()._is_tracking_enabled(main_object)
