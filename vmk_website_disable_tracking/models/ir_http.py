# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import models
from odoo.http import request


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    def _get_visitor_from_request(self, force_create=False, force_track_values=None):
        """No visitor on a website that does not track them.

        Every visitor Odoo records is made here, with `force_create`: by the
        tracker's route on a page view, and by forms that link what they create
        to the visitor, such as a CRM lead or an event registration. An empty
        recordset is what website returns when it finds none, so every caller
        already handles it: a lead or registration is simply made without a
        visitor. Existing visitors are not looked up either, so none is updated.
        """
        website = request and request.env and request.env.website
        if website and not website.vmk_track_visitors:
            return self.env["website.visitor"].sudo()
        return super()._get_visitor_from_request(force_create=force_create, force_track_values=force_track_values)
