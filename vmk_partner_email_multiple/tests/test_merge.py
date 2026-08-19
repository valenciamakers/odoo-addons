# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo.tests import tagged

from .common import PartnerEmailCase


@tagged("post_install", "-at_install")
class TestPartnerEmailMerge(PartnerEmailCase):
    def test_merge_keeps_the_source_address(self):
        duplicate = self.Partner.create(
            {"name": "Alice Example", "email": "alice.personal@example.com"}
        )
        self.Wizard._merge([self.alice.id, duplicate.id], dst_partner=self.alice)

        self.assertFalse(duplicate.exists(), "the source contact is gone")
        self.assertEqual(self.alice.email, "alice@example.com", "the primary is untouched")
        self.assertIn("alice.personal@example.com", self.alice.vmk_email_ids.mapped("email"))

    def test_merge_migrates_the_source_child_rows(self):
        """_update_foreign_keys re-points them in raw SQL, with no code from us."""
        duplicate = self.Partner.create(
            {
                "name": "Alice Example",
                "email": "alice.personal@example.com",
                "vmk_email_ids": [(0, 0, {"email": "alice.old@example.com"})],
            }
        )
        self.Wizard._merge([self.alice.id, duplicate.id], dst_partner=self.alice)
        self.assertIn("alice.old@example.com", self.alice.vmk_email_ids.mapped("email"))

    def test_merge_does_not_duplicate_an_address_already_held(self):
        duplicate = self.Partner.create(
            {"name": "Alice Example", "email": "alice.work@example.com"}
        )
        self.Wizard._merge([self.alice.id, duplicate.id], dst_partner=self.alice)
        rows = self.alice.vmk_email_ids.filtered(
            lambda r: r.email_normalized == "alice.work@example.com"
        )
        self.assertEqual(len(rows), 1)

    def test_merge_does_not_re_add_the_surviving_primary(self):
        duplicate = self.Partner.create(
            {"name": "Alice Example", "email": "alice.personal@example.com"}
        )
        self.Wizard._merge([self.alice.id, duplicate.id], dst_partner=self.alice)
        self.assertNotIn("alice@example.com", self.alice.vmk_email_ids.mapped("email"))

    def test_merge_keeps_an_unparseable_source_address(self):
        duplicate = self.Partner.create({"name": "Alice Example", "email": "no-at-sign"})
        self.Wizard._merge([self.alice.id, duplicate.id], dst_partner=self.alice)
        self.assertIn("no-at-sign", self.alice.vmk_email_ids.mapped("email"))

    def test_merge_without_a_named_destination(self):
        """Core picks the destination itself, so the addresses are captured for all."""
        duplicate = self.Partner.create(
            {"name": "Alice Example", "email": "alice.personal@example.com"}
        )
        self.Wizard._merge([self.alice.id, duplicate.id])

        survivor = (self.alice + duplicate).exists()
        self.assertEqual(len(survivor), 1)
        self.assertIn(
            "alice@example.com" if survivor == duplicate else "alice.personal@example.com",
            survivor.vmk_email_ids.mapped("email"),
        )

    def test_merged_contact_is_matchable_by_its_old_address(self):
        """The point of the whole exercise."""
        duplicate = self.Partner.create(
            {"name": "Alice Example", "email": "alice.personal@example.com"}
        )
        self.Wizard._merge([self.alice.id, duplicate.id], dst_partner=self.alice)

        before = self.Partner.search_count([])
        found = self.Partner._find_or_create_from_emails(["alice.personal@example.com"])
        self.assertEqual(found, [self.alice])
        self.assertEqual(self.Partner.search_count([]), before)
