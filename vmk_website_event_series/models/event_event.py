# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import api, models


class EventEvent(models.Model):
    _inherit = "event.event"

    @api.model
    def _search_get_detail(self, website, order, options):
        """The /event listing's Series filter: options["series"] is a
        series' id, or "all". It narrows the list and the counts beside the
        other filters, as each of website_event's own filters does."""
        detail = super()._search_get_detail(website, order, options)
        series = options.get("series")
        if series and series != "all":
            try:
                domain = [("series_id", "=", int(series))]
            except ValueError:
                return detail
            for key in ("base_domain", "no_date_domain", "no_country_domain"):
                if key in detail:
                    detail[key] = [*detail[key], domain]
        return detail
