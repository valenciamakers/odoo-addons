# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo.tests import tagged

from .common import PartnerEmailCase


@tagged("post_install", "-at_install")
class TestPromoteToPrimary(PartnerEmailCase):
    def test_promote_swaps_the_two_addresses(self):
        row = self.alice.vmk_email_ids.filtered(lambda r: r.label == "work")
        row.action_promote_to_primary()

        self.assertEqual(self.alice.email, "alice.work@example.com")
        self.assertEqual(row.email, "alice@example.com", "the old primary is kept, demoted")

    def test_promote_clears_the_label(self):
        """The label described the address that has just left."""
        row = self.alice.vmk_email_ids.filtered(lambda r: r.label == "work")
        row.action_promote_to_primary()
        self.assertFalse(row.label)

    def test_promote_leaves_the_other_rows_alone(self):
        row = self.alice.vmk_email_ids.filtered(lambda r: r.label == "work")
        row.action_promote_to_primary()
        self.assertIn("noreply@alice-shop.example.com", self.alice.vmk_email_ids.mapped("email"))

    def test_both_addresses_still_match_afterwards(self):
        row = self.alice.vmk_email_ids.filtered(lambda r: r.label == "work")
        row.action_promote_to_primary()

        found = self.Partner._find_or_create_from_emails(
            ["alice@example.com", "alice.work@example.com"], no_create=True
        )
        self.assertEqual(found, [self.alice, self.alice])

    def test_promote_with_no_primary_to_demote(self):
        bob = self.Partner.create(
            {
                "name": "Bob Example",
                "vmk_email_ids": [(0, 0, {"email": "bob@example.com"})],
            }
        )
        row = bob.vmk_email_ids
        row.action_promote_to_primary()

        self.assertEqual(bob.email, "bob@example.com")
        self.assertFalse(row.exists(), "no empty row is left behind")

    def test_promote_when_the_demoted_address_is_already_held(self):
        """Reachable if the primary was edited to an address already in the list."""
        bob = self.Partner.create({"name": "Bob Example", "email": "bob@example.com"})
        first = self.PartnerEmail.create({"partner_id": bob.id, "email": "bob.two@example.com"})
        second = self.PartnerEmail.create({"partner_id": bob.id, "email": "bob.three@example.com"})
        bob.email = "bob.three@example.com"

        first.action_promote_to_primary()

        self.assertEqual(bob.email, "bob.two@example.com")
        self.assertFalse(first.exists())
        self.assertTrue(second.exists(), "the row that already held it is the one kept")

    def test_promoting_is_tracked_in_the_chatter(self):
        # The fixture has to reach the database first. Tracking compares against
        # the value at the last flush, so a create and a write inside one flush
        # cycle show no delta -- an artifact of building the contact in the same
        # transaction, not of the swap.
        self.env.flush_all()
        self.cr.flush()

        row = self.alice.vmk_email_ids.filtered(lambda r: r.label == "work")
        before = self.env["mail.message"].search_count([
            ("model", "=", "res.partner"),
            ("res_id", "=", self.alice.id),
        ])
        row.action_promote_to_primary()
        # Tracking values are only materialised on flush, as mail's own
        # MailCommon.flush_tracking() does (mail/tests/common.py:1152).
        self.env.flush_all()
        self.cr.flush()

        after = self.env["mail.message"].search_count([
            ("model", "=", "res.partner"),
            ("res_id", "=", self.alice.id),
        ])
        self.assertGreater(after, before, "res.partner.email carries tracking=1")
