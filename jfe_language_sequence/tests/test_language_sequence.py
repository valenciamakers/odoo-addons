# Copyright 2026 Valencia Makers, SL
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestLanguageSequence(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ResLang = cls.env["res.lang"]
        cls.lang_en = cls.ResLang._activate_lang("en_US")
        cls.lang_es = cls.ResLang._activate_lang("es_ES")
        # Stock ordering is alphabetical, so English precedes Spanish by name.
        # Every assertion below is written to fail if the override stops working.

    def _installed_codes(self):
        return [code for code, _name in self.ResLang.get_installed()]

    def test_default_sequence_preserves_alphabetical_order(self):
        """Until something is dragged, ordering matches stock Odoo."""
        self.assertEqual(self.lang_en.sequence, self.lang_es.sequence)
        codes = self._installed_codes()
        self.assertLess(codes.index("en_US"), codes.index("es_ES"))

    def test_search_order_follows_sequence(self):
        self.lang_en.sequence = 20
        self.lang_es.sequence = 10
        langs = self.ResLang.search([("code", "in", ["en_US", "es_ES"])])
        self.assertEqual(langs.mapped("code"), ["es_ES", "en_US"])

    def test_get_installed_follows_sequence(self):
        """The language dropdowns on users and contacts follow the manual order."""
        self.lang_en.sequence = 20
        self.lang_es.sequence = 10
        codes = self._installed_codes()
        self.assertLess(codes.index("es_ES"), codes.index("en_US"))

    def test_resequencing_invalidates_the_cache(self):
        """``get_installed`` is served from an ormcache; it must not go stale."""
        self.lang_en.sequence = 20
        self.lang_es.sequence = 10
        codes = self._installed_codes()
        self.assertLess(codes.index("es_ES"), codes.index("en_US"))

        self.lang_en.sequence = 5
        codes = self._installed_codes()
        self.assertLess(codes.index("en_US"), codes.index("es_ES"))

    def test_frontend_selector_follows_sequence(self):
        """Outside a web request this exercises the http_routing code path."""
        self.lang_en.sequence = 20
        self.lang_es.sequence = 10
        codes = list(self.ResLang._get_frontend())
        self.assertLess(codes.index("es_ES"), codes.index("en_US"))

    def test_equal_sequences_fall_back_to_name(self):
        self.lang_en.sequence = 10
        self.lang_es.sequence = 10
        codes = self._installed_codes()
        self.assertLess(codes.index("en_US"), codes.index("es_ES"))

    def test_disabled_languages_never_precede_enabled_ones(self):
        """``active desc`` keeps the Languages list grouped as Odoo ships it."""
        disabled = self.ResLang.with_context(active_test=False).search(
            [("active", "=", False)], limit=1
        )
        self.assertTrue(disabled, "expected at least one disabled language")
        disabled.sequence = 1
        self.lang_en.sequence = 99
        langs = self.ResLang.with_context(active_test=False).search(
            [("id", "in", (disabled | self.lang_en).ids)]
        )
        self.assertEqual(langs.ids, (self.lang_en | disabled).ids)

    def test_sequence_is_cached_alongside_the_other_language_data(self):
        """Both ordering overrides read ``sequence`` off the cache, not the DB."""
        self.assertIn("sequence", self.ResLang.CACHED_FIELDS)
        self.lang_es.sequence = 42
        self.assertEqual(self.ResLang._get_data(code="es_ES").sequence, 42)
