# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from pathlib import Path

import polib

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestModuleNameTranslation(TransactionCase):
    """Guard the two catalogue entries for the module's own name and summary.

    They live on `ir.module.module` records whose `ir.model.data` row belongs
    to **base** (`ir_module.py` creates them as `base.module_<name>`). Odoo
    19's exporter omitted them, so they were kept by hand; Odoo 20's writes
    them, beside a `description` entry holding the whole README, which we
    leave out. `Manifest.get_translations` reads them from our PO files by
    their `#:` reference, even before the module is installed.

    `PoFileReader` still merges each PO against its module's POT and skips
    anything the merge marks obsolete -- so an entry missing from the POT is
    discarded in silence, translations and all, and the only symptom is the
    module showing an English name in a Spanish database.
    """

    MODULE = "vmk_website_event_slot_multiday"
    I18N = Path(__file__).resolve().parent.parent / "i18n"
    MODULE_METADATA = (
        "Multi-Day Event Slots (Website)",
        "Allow event slots to span multiple days, displayed on the website too",
    )

    def _translation(self, catalogue, msgid):
        """The msgstr of `msgid` in the catalogue, or None if the entry is absent.

        This reads the file rather than the database, where a dropped entry
        looks like nothing at all, and parses it with polib, as Odoo does,
        since the exporter wraps a long summary across lines.
        """
        entry = polib.pofile(str(self.I18N / catalogue)).find(msgid)
        return entry.msgstr if entry else None

    def test_the_pot_still_carries_them(self):
        for msgid in self.MODULE_METADATA:
            with self.subTest(msgid=msgid):
                self.assertIsNotNone(
                    self._translation(f"{self.MODULE}.pot", msgid),
                    "The POT has lost the module's name or summary. If you just "
                    f"re-exported it, check the two `base.module_{self.MODULE}` entries "
                    "survived -- without them the module name and summary silently stop "
                    "being translated. See the README's Translations section.",
                )

    def test_every_catalogue_translates_them(self):
        for catalogue in ("es.po", "ca.po"):
            for msgid in self.MODULE_METADATA:
                with self.subTest(catalogue=catalogue, msgid=msgid):
                    self.assertTrue(
                        self._translation(catalogue, msgid),
                        f"{catalogue} does not translate {msgid!r}.",
                    )

    def test_the_module_record_really_is_owned_by_base(self):
        """The premise the POT entries encode: the xmlid is base's, not ours.

        If Odoo ever moved these records into the module's own namespace,
        the entries' `base.module_*` references would stop matching.
        """
        data = self.env["ir.model.data"].search(
            [("model", "=", "ir.module.module"), ("name", "=", f"module_{self.MODULE}")]
        )
        self.assertEqual(data.module, "base")
