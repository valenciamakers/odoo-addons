# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from datetime import timedelta

from odoo import fields
from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestTours(HttpCase):

    def test_new_date(self):
        template = self.env["event.type"].create({"name": "Tour Template"})
        series = self.env["vmk.event.series"].create({
            "name": "Tour Series", "event_type_id": template.id,
        })
        self.env["event.event"].create({
            "name": "Tour Series",
            "series_id": series.id,
            "date_begin": fields.Datetime.now() + timedelta(days=5),
            "date_end": fields.Datetime.now() + timedelta(days=5, hours=2),
        })
        self.start_tour(
            f"/odoo/event-series/{series.id}", "vmk_event_series_new_date_tour", login="admin"
        )
