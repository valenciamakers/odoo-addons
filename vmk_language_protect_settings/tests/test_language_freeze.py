# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from pathlib import Path

from odoo.tests.common import TransactionCase, tagged
from odoo.tools.binary import BinaryBytes

from ..hooks import protect_enabled_languages

# A 1x1 transparent PNG; `fields.Image` rejects anything it cannot decode. Odoo 20's
# binary fields take a `BinaryValue` from Python, or base64 text as over RPC, never bytes.
ONE_PIXEL_PNG = BinaryBytes(
    bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
        "0000000d49444154789c6360000200000500010d0a2db40000000049454e44ae426082"
    )
)


@tagged("post_install", "-at_install")
class TestLanguageFreeze(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ResLang = cls.env["res.lang"]
        cls.lang_en = cls.ResLang._activate_lang("en_US")

    def _noupdate(self, lang):
        return (
            self.env["ir.model.data"]
            .sudo()
            .search([("model", "=", "res.lang"), ("res_id", "=", lang.id)])
            .noupdate
        )

    def _a_disabled_lang(self):
        return self.ResLang.with_context(active_test=False).search(
            [("active", "=", False)], limit=1
        )

    def test_enabled_languages_are_protected_on_install(self):
        self.assertTrue(self._noupdate(self.lang_en))
        self.assertTrue(self.lang_en.protect_from_updates)

    def test_editing_a_protected_field_protects_the_language(self):
        lang = self._a_disabled_lang()
        self.assertFalse(self._noupdate(lang))
        lang.name = "Something Custom"
        self.assertTrue(self._noupdate(lang))

    def test_editing_the_iso_code_protects_the_language(self):
        """The case this module was written for: broadening ca_ES to ca."""
        lang = self._a_disabled_lang()
        lang.iso_code = "xx"
        self.assertTrue(self._noupdate(lang))

    def test_editing_the_flag_protects_the_language(self):
        """`flag_image` is a stored image, and one of the fields `res_lang_data.xml` sets."""
        lang = self._a_disabled_lang()
        self.assertFalse(self._noupdate(lang))
        lang.flag_image = ONE_PIXEL_PNG
        self.assertTrue(self._noupdate(lang))

    def test_enabling_a_language_does_not_protect_it(self):
        """Activating is not a customisation; it must not freeze the record."""
        lang = self._a_disabled_lang()
        lang.active = True
        self.assertFalse(self._noupdate(lang))

    def test_the_data_loader_does_not_protect_anything(self):
        """Odoo re-applying its own data must not look like a user edit."""
        lang = self._a_disabled_lang()
        lang._load_records_write({"name": "Whatever Odoo Ships"})
        self.assertFalse(self._noupdate(lang))

    def test_the_install_hook_protects_enabled_languages(self):
        lang = self._a_disabled_lang()
        lang.active = True
        self.assertFalse(self._noupdate(lang))
        protect_enabled_languages(self.env)
        self.assertTrue(self._noupdate(lang))

    def test_the_flag_can_be_cleared_to_hand_control_back(self):
        self.assertTrue(self.lang_en.protect_from_updates)
        self.lang_en.protect_from_updates = False
        self.assertFalse(self._noupdate(self.lang_en))

    def test_a_hand_created_language_needs_no_protection(self):
        """It has no external id, so no data file can overwrite it."""
        lang = self.ResLang.create(
            {
                "name": "Klingon / tlhIngan Hol",
                "code": "tlh_KL",
                "iso_code": "tlh",
                "url_code": "tlh",
            }
        )
        self.assertFalse(lang.protect_from_updates)
        lang.name = "Klingon"
        self.assertFalse(lang.protect_from_updates)


@tagged("post_install", "-at_install")
class TestModuleNameTranslation(TransactionCase):
    """Guard the two catalogue entries for the module's own name and summary.

    They live on `ir.module.module` records whose `ir.model.data` row belongs to
    **base** (`ir_module.py` creates them as `base.module_<name>`). Odoo 19's
    exporter attributed them to base and omitted them from our POT, so they were
    in `i18n/` by hand; Odoo 20's exporter emits them itself. The guard stays,
    since the reader's merge against the POT is what makes a missing entry
    vanish in silence.

    That matters because `PoFileReader` merges each PO against its module's
    POT and skips anything the merge marks obsolete -- so an entry missing
    from the POT is discarded in silence, translations and all. Re-running
    `i18n export` overwrites the POT and would do exactly that. This test is
    what turns that into a failure instead of a quiet regression.
    """

    I18N = Path(__file__).resolve().parent.parent / "i18n"
    HAND_MAINTAINED = (
        "Protect Language Edits",
        "Stop Odoo updates from reverting your edits to language settings",
    )

    def test_pot_still_carries_the_hand_added_module_metadata(self):
        pot = (self.I18N / "vmk_language_protect_settings.pot").read_text(encoding="utf-8")
        for msgid in self.HAND_MAINTAINED:
            with self.subTest(msgid=msgid):
                self.assertIn(
                    f'msgid "{msgid}"',
                    pot,
                    "The POT has lost an entry for the module's name or summary. If you "
                    "just re-exported it, check the two `base.module_vmk_language_protect_settings` "
                    "blocks survived -- without them the module name and summary silently stop "
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
        entries' `base.module_*` references would stop matching.
        """
        data = self.env["ir.model.data"].search(
            [
                ("model", "=", "ir.module.module"),
                ("name", "=", "module_vmk_language_protect_settings"),
            ]
        )
        self.assertEqual(data.module, "base")
