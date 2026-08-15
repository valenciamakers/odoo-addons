# Copyright 2026 Valencia Makers, SL
# License MIT (https://opensource.org/licenses/MIT).

from pathlib import Path

from odoo.tests.common import TransactionCase, tagged


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
        "Language Metadata Protection",
        "Stop Odoo updates reverting your edits to language metadata",
    )

    def test_pot_still_carries_the_hand_added_module_metadata(self):
        pot = (self.I18N / "vmk_language_freeze_meta.pot").read_text(encoding="utf-8")
        for msgid in self.HAND_MAINTAINED:
            with self.subTest(msgid=msgid):
                self.assertIn(
                    f'msgid "{msgid}"',
                    pot,
                    "The POT has lost an entry `odoo i18n export` does not generate. If you "
                    "just re-exported it, re-add the two `base.module_vmk_language_freeze_meta` "
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
                ("name", "=", "module_vmk_language_freeze_meta"),
            ]
        )
        self.assertEqual(data.module, "base")
