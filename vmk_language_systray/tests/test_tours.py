# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo.tests.common import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestTours(HttpCase):
    """Drive the systray dropdown in a real browser; Python checks the outcome."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ResLang = cls.env["res.lang"]
        cls.admin = cls.env.ref("base.user_admin")

    def test_menu_lists_languages_and_switches(self):
        for code in ("es_ES", "ca_ES", "fr_FR"):
            self.ResLang._activate_lang(code)
        self.admin.lang = "en_US"
        self.start_tour("/odoo", "vmk_language_systray_menu", login="admin")
        self.assertEqual(self.admin.lang, "fr_FR")

    def test_single_language_hides_the_item(self):
        others = self.ResLang.search([("code", "!=", "en_US")])
        others.active = False
        self.assertEqual(self.ResLang.get_installed(), [("en_US", "English (US)")])
        self.admin.lang = "en_US"
        self.start_tour("/odoo", "vmk_language_systray_single_language", login="admin")
