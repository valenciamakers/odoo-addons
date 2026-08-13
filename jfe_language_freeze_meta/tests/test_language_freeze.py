# Copyright 2026 Valencia Makers, SL
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

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
