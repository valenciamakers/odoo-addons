# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from pathlib import Path

import polib

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
    """Guard the catalogue entries carrying the module's own name and summary.

    The module's name and summary live on an `ir.module.module` record whose
    `ir.model.data` row belongs to **base** (`ir_module.py` creates them as
    `base.module_<name>`). Odoo 19's exporter attributed them to base and left
    them out of our POT, so they were kept there by hand. Odoo 20's exporter
    writes them itself (`TranslationModuleReader._export_translatable_records`
    selects the `base.module_<name>` row of each exported module), and
    `Manifest.get_translations` reads them back from the module's own PO files
    by their `#:` reference, so a catalogue lacking that reference leaves the
    name in English on a module that is not installed yet.

    `PoFileReader` still merges each PO against its module's POT and skips
    whatever the merge marks obsolete, so an entry missing from the POT is
    still discarded in silence once the module is installed. These tests keep
    the entries, and their references, from going missing unnoticed.
    """

    I18N = Path(__file__).resolve().parent.parent / "i18n"
    MODULE_METADATA = (
        "Multiple Contact Emails",
        "Assign multiple email addresses to a contact, and Odoo matches mail from all of them",
    )

    REFERENCES = (
        "model:ir.module.module,shortdesc:base.module_vmk_partner_email_multiple",
        "model:ir.module.module,summary:base.module_vmk_partner_email_multiple",
    )

    def _entries(self, filename):
        """The entries by msgid: the exporter wraps long ones, so read them as a parser does."""
        return {e.msgid: e for e in polib.pofile(str(self.I18N / filename))}

    def test_pot_still_carries_the_module_metadata(self):
        entries = self._entries("vmk_partner_email_multiple.pot")
        for msgid, reference in zip(self.MODULE_METADATA, self.REFERENCES):
            with self.subTest(msgid=msgid):
                self.assertIn(
                    msgid,
                    entries,
                    "The POT has lost the module's name or summary. Re-export it with "
                    "`odoo i18n export`, which writes them on Odoo 20, or the module name and "
                    "summary silently stop being translated. See the README's Translations "
                    "section.",
                )
                self.assertIn(reference, [o for o, _ in entries[msgid].occurrences])

    def test_every_catalogue_translates_them(self):
        for po_name in ("es.po", "ca.po"):
            entries = self._entries(po_name)
            for msgid, reference in zip(self.MODULE_METADATA, self.REFERENCES):
                with self.subTest(po=po_name, msgid=msgid):
                    self.assertIn(msgid, entries)
                    self.assertTrue(entries[msgid].msgstr, "untranslated")
                    self.assertIn(reference, [o for o, _ in entries[msgid].occurrences])

    def test_the_module_record_really_is_owned_by_base(self):
        """The premise the `#:` references encode: the xmlid is base's, not ours.

        The catalogues name the record `base.module_vmk_partner_email_multiple`.
        If Odoo ever moved these records into the module's own namespace, every
        reference would stop matching.
        """
        data = self.env["ir.model.data"].search(
            [
                ("model", "=", "ir.module.module"),
                ("name", "=", "module_vmk_partner_email_multiple"),
            ]
        )
        self.assertEqual(data.module, "base")
