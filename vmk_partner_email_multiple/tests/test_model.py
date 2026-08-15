# Copyright 2026 Valencia Makers, SL
# License MIT (https://opensource.org/licenses/MIT).

from pathlib import Path

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged

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


@tagged("post_install", "-at_install")
class TestModuleNameTranslation(TransactionCase):
    """Guard the two catalogue entries `i18n export` will never regenerate.

    The module's own name and summary live on `ir.module.module` records whose
    `ir.model.data` row belongs to **base** (`ir_module.py` creates them as
    `base.module_<name>`), so the exporter attributes them to base and omits
    them from our POT. They are in `i18n/` by hand.

    That matters because `PoFileReader` merges each PO against its module's
    POT and skips anything the merge marks obsolete -- so an entry missing
    from the POT is discarded in silence, translations and all. Re-running
    `i18n export` overwrites the POT and would do exactly that. This test is
    what turns that into a failure instead of a quiet regression.
    """

    I18N = Path(__file__).resolve().parent.parent / "i18n"
    HAND_MAINTAINED = (
        "Multiple Contact Emails",
        "Several email addresses per contact, matched by Odoo's own machinery",
    )

    def test_pot_still_carries_the_hand_added_module_metadata(self):
        pot = (self.I18N / "vmk_partner_email_multiple.pot").read_text(encoding="utf-8")
        for msgid in self.HAND_MAINTAINED:
            with self.subTest(msgid=msgid):
                self.assertIn(
                    f'msgid "{msgid}"',
                    pot,
                    "The POT has lost an entry `odoo i18n export` does not generate. If you "
                    "just re-exported it, re-add the two `base.module_vmk_partner_email_multiple` "
                    "blocks by hand -- without them the module name and summary silently stop "
                    "being translated. See the README's Translations section.",
                )

    def test_every_catalogue_translates_them(self):
        for po_name in ("es.po", "ca.po"):
            po = (self.I18N / po_name).read_text(encoding="utf-8")
            for msgid in self.HAND_MAINTAINED:
                with self.subTest(po=po_name, msgid=msgid):
                    self.assertIn(f'msgid "{msgid}"', po)

    def test_the_module_record_really_is_owned_by_base(self):
        """The premise the POT entries encode: the xmlid is base's, not ours.

        If Odoo ever attributes these records to the module itself, the
        exporter would start emitting them and the hand-maintenance above
        becomes not just unnecessary but actively wrong.
        """
        data = self.env["ir.model.data"].search(
            [
                ("model", "=", "ir.module.module"),
                ("name", "=", "module_vmk_partner_email_multiple"),
            ]
        )
        self.assertEqual(data.module, "base")
