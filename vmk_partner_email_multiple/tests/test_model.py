# Copyright 2026 Valencia Makers, SL
# License MIT (https://opensource.org/licenses/MIT).

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import PartnerEmailCase


@tagged("post_install", "-at_install")
class TestPartnerEmailModel(PartnerEmailCase):
    def test_email_normalized_is_computed(self):
        row = self.alice.vmk_email_ids.filtered(lambda r: r.label == "work")
        self.assertEqual(row.email_normalized, "alice.work@example.com")

        row.email = "  Alice WORK <Alice.Work@Example.COM>  "
        self.assertEqual(
            row.email_normalized,
            "alice.work@example.com",
            "the display-name form should normalize the same way core does",
        )

    def test_unparseable_address_is_stored_without_a_normalized_value(self):
        row = self.PartnerEmail.create({"partner_id": self.alice.id, "email": "not an address"})
        self.assertFalse(row.email_normalized)

    def test_duplicate_of_another_additional_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.PartnerEmail.create(
                {"partner_id": self.alice.id, "email": "ALICE.WORK@example.com"}
            )

    def test_duplicate_of_the_primary_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.PartnerEmail.create(
                {"partner_id": self.alice.id, "email": "Alice <alice@example.com>"}
            )

    def test_same_address_on_two_contacts_is_allowed(self):
        """Core permits it and the mail helpers tie-break for it, so we do not forbid it."""
        bob = self.Partner.create({"name": "Bob Example", "email": "bob@example.com"})
        shared = self.PartnerEmail.create(
            {"partner_id": bob.id, "email": "alice.work@example.com"}
        )
        self.assertTrue(shared.id)

    def test_rows_are_removed_with_the_contact(self):
        bob = self.Partner.create(
            {
                "name": "Bob Example",
                "email": "bob@example.com",
                "vmk_email_ids": [(0, 0, {"email": "bob.other@example.com"})],
            }
        )
        row = bob.vmk_email_ids
        bob.unlink()
        self.assertFalse(row.exists(), "ondelete='cascade' should take the rows with it")
