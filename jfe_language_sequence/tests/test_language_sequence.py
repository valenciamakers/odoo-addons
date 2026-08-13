# Copyright 2026 Valencia Makers, SL
# License MIT (https://opensource.org/licenses/MIT).

from odoo.addons.jfe_language_sequence.hooks import seed_language_sequence
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

    def test_seeding_reproduces_stock_alphabetical_order(self):
        """As installed, before anything is dragged, ordering matches stock Odoo.

        Seeding is re-run here rather than relying on the ambient state: the
        sequences on a database that has been in use are whatever its users
        dragged them to, which is the whole point of the module.
        """
        seed_language_sequence(self.env)
        enabled = self.ResLang.search([("active", "=", True)], order="sequence")
        self.assertEqual(
            enabled.mapped("code"), enabled.sorted("name").mapped("code")
        )

    def test_enabled_languages_are_seeded_ahead_of_disabled_ones(self):
        """The Languages list is ordered `sequence, id`, so the values must group."""
        all_langs = self.ResLang.with_context(active_test=False)
        enabled = all_langs.search([("active", "=", True)])
        disabled = all_langs.search([("active", "=", False)])
        self.assertLess(
            max(enabled.mapped("sequence")), min(disabled.mapped("sequence"))
        )

    def test_seeded_sequences_are_distinct(self):
        """Tied values make Odoo resequence the whole list on the first drag."""
        sequences = self.ResLang.with_context(active_test=False).search([]).mapped(
            "sequence"
        )
        self.assertEqual(len(sequences), len(set(sequences)))

    def test_enabling_a_language_joins_the_enabled_block(self):
        all_langs = self.ResLang.with_context(active_test=False)
        newcomer = all_langs.search([("active", "=", False)], limit=1)
        newcomer.active = True
        others = all_langs.search([("active", "=", True), ("id", "!=", newcomer.id)])
        still_disabled = all_langs.search([("active", "=", False)])
        self.assertGreater(newcomer.sequence, max(others.mapped("sequence")))
        self.assertLess(newcomer.sequence, min(still_disabled.mapped("sequence")))

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

    def _create_lang(self, **vals):
        """A language Odoo does not ship, added by hand."""
        return self.ResLang.create(
            {
                "name": "Klingon / tlhIngan Hol",
                "code": "tlh_KL",
                "iso_code": "tlh",
                "url_code": "tlh",
                **vals,
            }
        )

    def test_a_hand_created_language_lands_in_the_disabled_block(self):
        all_langs = self.ResLang.with_context(active_test=False)
        newcomer = self._create_lang()
        self.assertFalse(newcomer.active, "res.lang has no default for `active`")
        enabled = all_langs.search([("active", "=", True)])
        self.assertGreater(newcomer.sequence, max(enabled.mapped("sequence")))

    def test_a_hand_created_enabled_language_joins_the_enabled_block(self):
        all_langs = self.ResLang.with_context(active_test=False)
        newcomer = self._create_lang(active=True)
        others = all_langs.search([("active", "=", True), ("id", "!=", newcomer.id)])
        disabled = all_langs.search([("active", "=", False)])
        self.assertGreater(newcomer.sequence, max(others.mapped("sequence")))
        self.assertLess(newcomer.sequence, min(disabled.mapped("sequence")))

    def test_creating_a_language_keeps_sequences_distinct(self):
        """Ties would cost the localised drag the seeding exists to protect."""
        self._create_lang()
        sequences = self.ResLang.with_context(active_test=False).search([]).mapped(
            "sequence"
        )
        self.assertEqual(len(sequences), len(set(sequences)))

    def test_an_explicit_sequence_on_create_is_respected(self):
        self.assertEqual(self._create_lang(sequence=7).sequence, 7)

    def test_the_field_default_sits_in_the_disabled_block(self):
        """The default is the fallback if parking on create ever fails."""
        default = self.ResLang.default_get(["sequence"])["sequence"]
        enabled = self.ResLang.search([("active", "=", True)])
        self.assertGreater(default, max(enabled.mapped("sequence")))

    def test_sequence_is_cached_alongside_the_other_language_data(self):
        """Both ordering overrides read ``sequence`` off the cache, not the DB."""
        self.assertIn("sequence", self.ResLang.CACHED_FIELDS)
        self.lang_es.sequence = 42
        self.assertEqual(self.ResLang._get_data(code="es_ES").sequence, 42)
