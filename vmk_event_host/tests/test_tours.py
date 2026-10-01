# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import Command
from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestTours(HttpCase):
    """Drive the event form and list in a real browser."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Zoe sorts after Ada, so a summary reading "Zoe, Ada" proves the order
        # is the lines' own rather than the contacts'.
        cls.zoe, cls.ada, cls.grace = cls.env["res.partner"].create(
            [
                {"name": "Zoe Zapata"},
                {"name": "Ada Lovelace"},
                {"name": "Grace Hopper"},
            ]
        )
        cls.event = cls.env["event.event"].create(
            {
                "name": "Intro to 3D Printing",
                "date_begin": "2026-10-05 16:00:00",
                "date_end": "2026-10-05 18:30:00",
                "vmk_host_ids": [
                    Command.create({"partner_id": cls.zoe.id, "role": "Lead"}),
                    Command.create({"partner_id": cls.ada.id}),
                ],
            }
        )
        cls.solder = cls.env["event.event"].create(
            {
                "name": "Soldering Basics",
                "date_begin": "2026-10-06 16:00:00",
                "date_end": "2026-10-06 18:30:00",
                "vmk_host_ids": [Command.create({"partner_id": cls.ada.id})],
            }
        )
        cls.cnc = cls.env["event.event"].create(
            {
                "name": "CNC Night",
                "date_begin": "2026-10-07 16:00:00",
                "date_end": "2026-10-07 18:30:00",
            }
        )

    def _form_url(self, event):
        return f"/odoo/action-event.action_event_view/{event.id}"

    def test_summary_opens_the_hosts_tab(self):
        self.start_tour(self._form_url(self.event), "vmk_event_host_summary_tour", login="admin")

    def test_add_a_host(self):
        self.start_tour(self._form_url(self.event), "vmk_event_host_add_tour", login="admin")
        self.assertEqual(
            self.event.vmk_host_ids.mapped("partner_id"), self.zoe + self.ada + self.grace
        )
        added = self.event.vmk_host_ids[-1]
        self.assertEqual(added.role, "Guest speaker")
        self.assertEqual(
            self.event.vmk_host_names,
            "Zoe Zapata (Lead), Ada Lovelace, Grace Hopper (Guest speaker)",
        )

    def test_reorder_hosts(self):
        self.start_tour(self._form_url(self.event), "vmk_event_host_reorder_tour", login="admin")
        self.event.invalidate_recordset()
        self.assertEqual(self.event.vmk_host_ids.partner_id, self.ada + self.zoe)
        self.assertEqual(self.event.vmk_host_names, "Ada Lovelace, Zoe Zapata (Lead)")

    def test_search_by_host(self):
        self.start_tour("/odoo/events?view_type=list", "vmk_event_host_search_tour", login="admin")

    def test_group_by_host(self):
        self.start_tour("/odoo/events?view_type=list", "vmk_event_host_group_tour", login="admin")
