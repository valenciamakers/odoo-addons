# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import Command
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestEventHost(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partners = cls.env["res.partner"].create(
            [{"name": "Ada Lovelace"}, {"name": "Grace Hopper"}]
        )
        cls.event = cls.env["event.event"].create(
            {
                "name": "Intro to 3D Printing",
                "date_begin": "2026-10-05 16:00:00",
                "date_end": "2026-10-05 18:30:00",
                "vmk_host_ids": [Command.set(cls.partners.ids)],
            }
        )

    def test_several_hosts_are_stored(self):
        """An event keeps every host it was given, not just the last one."""
        self.assertEqual(self.event.vmk_host_ids, self.partners)

    def test_hosts_are_searchable(self):
        """Searching by one host finds the event, which is what the search view relies on."""
        found = self.env["event.event"].search(
            [("vmk_host_ids", "in", self.partners[0].ids)]
        )
        self.assertIn(self.event, found)

    def test_grouping_by_host_lists_the_event_under_each(self):
        """The Group by > Host filter puts a co-hosted event under both hosts."""
        groups = self.env["event.event"]._read_group(
            domain=[("id", "=", self.event.id)],
            groupby=["vmk_host_ids"],
            aggregates=["id:count"],
        )
        self.assertEqual({partner for partner, _count in groups}, set(self.partners))

    def test_host_changes_are_tracked(self):
        """Hosts reach the chatter, as Responsible and Organizer already do."""
        self.assertIn("vmk_host_ids", self.env["event.event"]._track_get_fields())

    def test_form_view_carries_the_field(self):
        """A misplaced xpath fails here rather than silently dropping the field."""
        arch = self.env["event.event"].get_view(
            view_id=self.env.ref("event.view_event_form").id
        )["arch"]
        self.assertIn("vmk_host_ids", arch)

    def test_search_view_offers_grouping(self):
        """The group-by filter survives inheritance into core's search view."""
        arch = self.env["event.event"].get_view(
            view_id=self.env.ref("event.view_event_search").id, view_type="search"
        )["arch"]
        self.assertIn("'group_by': 'vmk_host_ids'", arch)
