# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import Command
from odoo.tests.common import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestTours(HttpCase):
    """Drive the order of the languages in a real browser.

    The sequences are deliberately not alphabetical: French, English, Catalan,
    Spanish, where by name it would be Catalan, English, French, Spanish.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        ResLang = cls.env["res.lang"]
        cls.fr, cls.en, cls.ca, cls.es = (
            ResLang._activate_lang(code) for code in ("fr_FR", "en_US", "ca_ES", "es_ES")
        )
        for lang, sequence in zip((cls.fr, cls.en, cls.ca, cls.es), (10, 20, 30, 40)):
            lang.sequence = sequence
        # Every other enabled language would join the lists and muddy the order.
        ResLang.search([("id", "not in", (cls.fr + cls.en + cls.ca + cls.es).ids)]).active = False
        cls.codes = ("fr_FR", "en_US", "ca_ES", "es_ES")

    def _offer_on_the_website(self):
        """Put the four languages on the website, or skip where there is none."""
        if "website" not in self.env:
            self.skipTest("website is not installed")
        self.env.ref("website.default_website").language_ids = [
            Command.set((self.fr + self.en + self.ca + self.es).ids)
        ]

    def test_systray_menu_follows_sequence(self):
        if not self.env["ir.module.module"].search_count(
            [("name", "=", "vmk_language_systray"), ("state", "=", "installed")]
        ):
            self.skipTest("vmk_language_systray is not installed")
        self.assertEqual([c for c, _ in self.env["res.lang"].get_installed()], list(self.codes))
        self.start_tour("/odoo", "vmk_language_sequence_systray", login="admin")

    def test_website_selector_follows_sequence(self):
        self._offer_on_the_website()
        self.start_tour("/", "vmk_language_sequence_website_selector")

    def test_website_selector_follows_sequence_when_logged_in(self):
        self._offer_on_the_website()
        self.start_tour("/", "vmk_language_sequence_website_selector", login="admin")

    def test_dragging_in_the_languages_list_resequences(self):
        self.start_tour(
            "/odoo/action-base.res_lang_act_window?debug=1",
            "vmk_language_sequence_drag",
            login="admin",
        )
        ordered = self.env["res.lang"].search([("active", "=", True)], order="sequence, id")
        self.assertEqual(
            ordered.mapped("code"), ["en_US", "ca_ES", "fr_FR", "es_ES"]
        )
        self.assertEqual(
            [c for c, _ in self.env["res.lang"].get_installed()],
            ["en_US", "ca_ES", "fr_FR", "es_ES"],
        )
