# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestEventHost(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Named so that alphabetical order is the reverse of the order they are
        # added in: the whole point of the line model is that insertion order,
        # not the contacts' own order, is what survives.
        cls.zoe, cls.ada = cls.env["res.partner"].create(
            [{"name": "Zoe Zapata"}, {"name": "Ada Lovelace"}]
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

    def test_hosts_keep_the_order_they_were_added_in(self):
        """Not the contacts' alphabetical order, which is what a many2many gave."""
        self.assertEqual(self.event.vmk_host_ids.partner_id, self.zoe + self.ada)

    def test_hosts_can_be_reordered(self):
        """Writing sequence is what the drag handle does."""
        first, second = self.event.vmk_host_ids
        first.sequence, second.sequence = 20, 10
        self.assertEqual(self.event.vmk_host_ids.partner_id, self.ada + self.zoe)

    def test_editing_only_a_role_updates_the_summary(self):
        """The summary prints each line's display name, which carries the role,
        so a role edited alone has to recompute it."""
        self.assertIn("Zoe Zapata (Lead)", self.event.vmk_host_names)
        self.event.vmk_host_ids[0].role = "Assistant"
        self.assertIn("Zoe Zapata (Assistant)", self.event.vmk_host_names)
        self.assertNotIn("(Lead)", self.event.vmk_host_names)

    def test_a_contact_cannot_host_the_same_event_twice(self):
        """A Python constraint, not a SQL one: see the merge tests below."""
        with self.assertRaises(ValidationError):
            self.env["vmk.event.host"].create(
                {"event_id": self.event.id, "partner_id": self.zoe.id}
            )

    def test_merging_two_hosts_keeps_their_other_events(self):
        """The merge wizard re-points partner foreign keys in raw SQL and, on a
        table with a unique constraint on that column, deletes every merged
        contact's row when one collides. With Zoe and Ada co-hosting this
        event, merging them used to lose Ada's line on every other event."""
        other = self.env["event.event"].create(
            {
                "name": "Advanced 3D Printing",
                "date_begin": "2026-10-06 16:00:00",
                "date_end": "2026-10-06 18:30:00",
                "vmk_host_ids": [Command.create({"partner_id": self.ada.id})],
            }
        )
        self.env["base.partner.merge.automatic.wizard"]._merge(
            [self.zoe.id, self.ada.id], dst_partner=self.zoe
        )
        self.assertFalse(self.ada.exists())
        self.assertEqual(other.vmk_host_ids.partner_id, self.zoe)
        self.assertEqual(other.vmk_host_partner_ids, self.zoe, "the mirror follows")
        self.assertEqual(other.vmk_host_names, "Zoe Zapata")

    def test_merging_co_hosts_leaves_one_line(self):
        """The bulk UPDATE compares no values, so the survivor held the event
        twice until something deduplicated it."""
        self.env["base.partner.merge.automatic.wizard"]._merge(
            [self.zoe.id, self.ada.id], dst_partner=self.zoe
        )
        self.assertEqual(len(self.event.vmk_host_ids), 1)
        self.assertEqual(self.event.vmk_host_ids.partner_id, self.zoe)
        self.assertEqual(self.event.vmk_host_ids.role, "Lead", "the survivor's own line is kept")
        self.assertEqual(self.event.vmk_host_partner_ids, self.zoe)
        self.assertEqual(self.event.vmk_host_names, "Zoe Zapata (Lead)")
        # The constraint sees a clean table again.
        with self.assertRaises(ValidationError):
            self.env["vmk.event.host"].create(
                {"event_id": self.event.id, "partner_id": self.zoe.id}
            )

    def test_merging_keeps_the_surviving_contacts_own_line(self):
        """Whichever line sorts first: the survivor's role and position stay,
        as the merge keeps the survivor's name and email."""
        zoe_line, ada_line = self.event.vmk_host_ids
        ada_line.sequence = 5  # Ada's line now sorts before Zoe's
        self.env["base.partner.merge.automatic.wizard"]._merge(
            [self.zoe.id, self.ada.id], dst_partner=self.zoe
        )
        self.assertEqual(self.event.vmk_host_ids, zoe_line)
        self.assertEqual(self.event.vmk_host_ids.role, "Lead")
        self.assertFalse(ada_line.exists())

    def test_merging_into_the_other_contact_keeps_its_line_instead(self):
        zoe_line, ada_line = self.event.vmk_host_ids
        self.env["base.partner.merge.automatic.wizard"]._merge(
            [self.zoe.id, self.ada.id], dst_partner=self.ada
        )
        self.assertFalse(self.zoe.exists())
        self.assertEqual(self.event.vmk_host_ids, ada_line)
        self.assertFalse(self.event.vmk_host_ids.role, "Ada's own line had no role, and keeps none")
        self.assertEqual(self.event.vmk_host_names, "Ada Lovelace")

    def test_role_is_optional_and_shown_in_the_name(self):
        lead, plain = self.event.vmk_host_ids
        self.assertEqual(lead.display_name, "Zoe Zapata (Lead)")
        self.assertEqual(plain.display_name, "Ada Lovelace")

    def test_summary_shows_hosts_in_their_own_order(self):
        """The form header reads this, so it must not fall back to alphabetical."""
        self.assertEqual(
            self.event.vmk_host_names, "Zoe Zapata (Lead), Ada Lovelace"
        )
        first, second = self.event.vmk_host_ids
        first.sequence, second.sequence = 20, 10
        self.assertEqual(
            self.event.vmk_host_names, "Ada Lovelace, Zoe Zapata (Lead)"
        )

    def test_mirror_field_follows_the_lines(self):
        """The searchable mirror is what the search view and list column read."""
        self.assertEqual(self.event.vmk_host_partner_ids, self.zoe + self.ada)
        self.event.vmk_host_ids[0].unlink()
        self.assertEqual(self.event.vmk_host_partner_ids, self.ada)

    def test_hosts_are_searchable(self):
        found = self.env["event.event"].search(
            [("vmk_host_partner_ids", "in", self.ada.ids)]
        )
        self.assertIn(self.event, found)

    def test_grouping_by_host_lists_the_event_under_each(self):
        """A co-hosted event appears under both hosts."""
        groups = self.env["event.event"]._read_group(
            domain=[("id", "=", self.event.id)],
            groupby=["vmk_host_partner_ids"],
            aggregates=["id:count"],
        )
        self.assertEqual(
            {partner for partner, _count in groups}, {self.zoe, self.ada}
        )

    def test_host_changes_are_tracked(self):
        """Hosts reach the chatter, as Responsible and Organizer already do."""
        self.assertIn(
            "vmk_host_partner_ids", self.env["event.event"]._track_get_fields()
        )

    def test_deleting_the_event_takes_its_host_lines(self):
        host_ids = self.event.vmk_host_ids.ids
        self.event.unlink()
        self.assertFalse(self.env["vmk.event.host"].browse(host_ids).exists())

    def test_form_view_carries_the_hosts_tab(self):
        """A misplaced xpath fails here rather than silently dropping the field."""
        arch = self.env["event.event"].get_view(
            view_id=self.env.ref("event.view_event_form").id
        )["arch"]
        self.assertIn("vmk_host_ids", arch)
        self.assertIn("vmk_hosts", arch)

    def test_search_view_offers_grouping(self):
        arch = self.env["event.event"].get_view(
            view_id=self.env.ref("event.view_event_search").id, view_type="search"
        )["arch"]
        self.assertIn("'group_by': 'vmk_host_partner_ids'", arch)
