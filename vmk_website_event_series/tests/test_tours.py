# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from datetime import timedelta

from odoo import fields
from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestTours(HttpCase):

    def test_filter_and_links(self):
        now = fields.Datetime.now()
        series = self.env["vmk.event.series"].create({"name": "VMK Tour Series", "is_published": True})
        self.env["event.event"].create([
            {
                "name": name,
                "series_id": series_id,
                "date_begin": now + timedelta(days=days),
                "date_end": now + timedelta(days=days, hours=2),
                "is_published": True,
            }
            for name, series_id, days in (
                ("VMK Tour Date", series.id, 2),
                ("VMK Tour Other", False, 3),
            )
        ])
        self.start_tour("/event?country=all", "vmk_website_event_series_filter_tour")
