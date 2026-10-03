# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from pathlib import Path
from unittest import SkipTest

from odoo.addons.http_routing.tests.common import MockRequest
from odoo.addons.vmk_language_sequence.hooks import seed_language_sequence
from odoo.addons.vmk_language_sequence.models.res_lang import PATCHED
from odoo.fields import Command
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

    def test_the_contact_language_selection_follows_sequence(self):
        """The dropdown on a contact's form is built from ``get_installed()``."""
        self.lang_en.sequence = 20
        self.lang_es.sequence = 10
        selection = self.env["res.partner"]._fields["lang"]._description_selection(self.env)
        codes = [code for code, _name in selection]
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
        """The ordering reads ``sequence`` off the cache, not the DB."""
        self.assertIn("sequence", self.ResLang._cached_data_fields)
        self.assertIn("name", self.ResLang._cached_data_fields, "core's own fields are kept")
        self.lang_es.sequence = 42
        self.assertEqual(self.ResLang._get_data(code="es_ES").sequence, 42)

    def test_writing_a_sequence_clears_the_language_cache(self):
        """Core clears 'stable' only for ``_clear_cache_on_fields``; ours must be in it."""
        self.assertIn("sequence", self.ResLang._clear_cache_on_fields)
        self.lang_en.sequence = 20
        self.lang_es.sequence = 10
        codes = list(self.ResLang._get_active_by("code"))
        self.assertLess(codes.index("es_ES"), codes.index("en_US"))
        self.lang_en.sequence = 5
        codes = list(self.ResLang._get_active_by("code"))
        self.assertLess(codes.index("en_US"), codes.index("es_ES"))

    def test_every_keyed_view_of_the_cache_follows_sequence(self):
        """``_get_active_by`` is keyed by code, id or URL code, all in our order."""
        self.lang_en.sequence = 20
        self.lang_es.sequence = 10
        for field in ("code", "id", "url_code"):
            with self.subTest(field=field):
                keys = list(self.ResLang._get_active_by(field))
                es, en = (
                    getattr(self.lang_es, field),
                    getattr(self.lang_en, field),
                )
                self.assertLess(keys.index(es), keys.index(en))

    def test_active_langs_follow_sequence(self):
        self.lang_en.sequence = 20
        self.lang_es.sequence = 10
        langs = self.ResLang._get_active_langs()
        self.assertLess(langs.ids.index(self.lang_es.id), langs.ids.index(self.lang_en.id))
        self.assertEqual(set(langs.ids), set(self.ResLang.get_all().ids))

    def test_the_sequence_reaches_a_language_without_a_cached_entry(self):
        """A disabled language is not in the cache; reading it falls through to the DB."""
        disabled = self.ResLang.with_context(active_test=False).search(
            [("active", "=", False)], limit=1
        )
        disabled.sequence = 4242
        self.assertEqual(disabled.sequence, 4242)

    def test_unknown_language_data_is_still_a_dummy(self):
        """Core's dummy entry for a missing key, which ``_get_frontend`` does not rely on."""
        self.assertFalse(self.ResLang._get_data(code="xx_XX"))

    def test_disabling_a_language_drops_it_from_the_dropdowns(self):
        lang_fr = self.ResLang._activate_lang("fr_FR")
        self.assertIn("fr_FR", self._installed_codes())
        lang_fr.active = False
        self.assertNotIn("fr_FR", self._installed_codes())


@tagged("post_install", "-at_install")
class TestFrontendPatch(TransactionCase):
    """``_get_frontend`` is ours on the registry class, above every module's.

    Nothing raises if the patch stops applying: the site selector just goes back
    to name order, and only where ``website`` is installed.
    """

    def test_the_registry_class_carries_our_method(self):
        model_cls = self.env.registry["res.lang"]
        # In the class's own ``__dict__``, not inherited: that is what puts it
        # above ``website``'s override whichever module loaded first.
        self.assertIn("_get_frontend", model_cls.__dict__)
        self.assertTrue(getattr(model_cls.__dict__["_get_frontend"], PATCHED, False))

    def test_a_second_hook_call_does_not_wrap_it_again(self):
        model_cls = self.env.registry["res.lang"]
        before = model_cls.__dict__["_get_frontend"]
        self.env["res.lang"]._register_hook()
        self.assertIs(model_cls.__dict__["_get_frontend"], before)


@tagged("post_install", "-at_install")
class TestHreflang(TransactionCase):
    """The generic hreflang code goes to the first variant in your order, not by name.

    Written the way ``website``'s own ``test_alternate_hreflang`` is, which fails
    with this module installed because it asserts the name order. Only ``website``
    hands out hreflang codes, so this is skipped on a database without it.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Odoo 20 keeps the ``website`` model in ``base``; its languages are the
        # ``website`` module's.
        if "language_ids" not in cls.env["website"]._fields:
            raise SkipTest("website is not installed")
        cls.website = cls.env.ref("base.default_website")
        cls.ResLang = cls.env["res.lang"].with_context(website_id=cls.website.id)
        cls.lang_us = cls.ResLang._activate_lang("en_US")
        cls.lang_uk = cls.ResLang._activate_lang("en_GB")

    def _hreflangs(self, langs):
        self.website.language_ids = [Command.set(langs.ids)]
        with MockRequest(self.env, website=self.website):
            return {code: data.hreflang for code, data in self.ResLang._get_frontend().items()}

    def test_the_site_selector_follows_sequence_for_the_current_website(self):
        """``website``'s own branch, which sorts by name, is reordered and stays fresh."""
        lang_es = self.ResLang._activate_lang("es_ES")
        langs = self.lang_us + self.lang_uk + lang_es
        self.lang_us.sequence, self.lang_uk.sequence, lang_es.sequence = 10, 20, 30
        self.assertEqual(list(self._hreflangs(langs)), ["en_US", "en_GB", "es_ES"])
        # By name the order would be en_GB, en_US, es_ES; a later drag must show at once.
        lang_es.sequence, self.lang_uk.sequence = 5, 25
        self.assertEqual(list(self._hreflangs(langs)), ["es_ES", "en_US", "en_GB"])

    def test_the_first_variant_in_your_order_is_generic(self):
        langs = self.lang_us + self.lang_uk
        self.lang_us.sequence, self.lang_uk.sequence = 10, 20
        self.assertEqual(self._hreflangs(langs), {"en_US": "en", "en_GB": "en-gb"})
        # By name, English (UK) would be generic in both cases.
        self.lang_us.sequence, self.lang_uk.sequence = 20, 10
        self.assertEqual(self._hreflangs(langs), {"en_US": "en-us", "en_GB": "en"})

    def test_latin_american_spanish_stays_generic_as_in_core(self):
        lang_es = self.ResLang._activate_lang("es_ES")
        lang_419 = self.ResLang._activate_lang("es_419")
        lang_es.sequence, lang_419.sequence = 10, 20
        hreflangs = self._hreflangs(self.lang_us + lang_es + lang_419)
        self.assertEqual(hreflangs["es_419"], "es")
        self.assertEqual(hreflangs["es_ES"], "es-es")

    def test_without_a_current_website_no_hreflang_is_added(self):
        """Odoo 19 keyed this on the request; 20 keys it on ``env.website``."""
        self.assertFalse(self.env["res.lang"].env.website)
        for data in self.env["res.lang"]._get_frontend().values():
            self.assertNotIn("hreflang", data)


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
    from the POT is discarded in silence, translations and all. This test is
    what turns that into a failure instead of a quiet regression.
    """

    I18N = Path(__file__).resolve().parent.parent / "i18n"
    HAND_MAINTAINED = (
        "Language Sequence",
        "Reorder languages manually instead of alphabetically",
    )

    def test_pot_still_carries_the_hand_added_module_metadata(self):
        pot = (self.I18N / "vmk_language_sequence.pot").read_text(encoding="utf-8")
        for msgid in self.HAND_MAINTAINED:
            with self.subTest(msgid=msgid):
                self.assertIn(
                    f'msgid "{msgid}"',
                    pot,
                    "The POT has lost an entry for the module's name or summary. If you "
                    "just re-exported it, check the two `base.module_vmk_language_sequence` "
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
            [("model", "=", "ir.module.module"), ("name", "=", "module_vmk_language_sequence")]
        )
        self.assertEqual(data.module, "base")
