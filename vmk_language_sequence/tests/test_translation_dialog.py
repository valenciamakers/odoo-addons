# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo.tests.common import HttpCase, tagged

ROUTE = "/web/translations/get_translation_for_field"


@tagged("post_install", "-at_install")
class TestTranslationDialog(HttpCase):
    """The translation dialog's payload lists the languages in their sequence.

    Asked over HTTP, as the dialog asks, because the order has to survive the
    JSON response: the client draws the ``languages`` object in the order its
    keys arrive. The sequences are not alphabetical: French, English, Catalan,
    Spanish, where by name it would be Catalan, English, French, Spanish.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        ResLang = cls.env["res.lang"]
        cls.codes = ["fr_FR", "en_US", "ca_ES", "es_ES"]
        langs = ResLang.browse()
        for sequence, code in enumerate(cls.codes, start=1):
            lang = ResLang._activate_lang(code)
            lang.sequence = sequence * 10
            langs |= lang
        # Every other enabled language would join the lists and muddy the order.
        ResLang.search([("id", "not in", langs.ids)]).active = False

    def _payload(self, record, field_name):
        self.authenticate("admin", "admin")
        return self.make_jsonrpc_request(
            ROUTE,
            {"res_model": record._name, "res_id": record.id, "field_name": field_name},
        )

    def test_a_plain_field_lists_languages_and_terms_in_sequence(self):
        payload = self._payload(self.env.ref("base.es"), "name")
        self.assertEqual(payload["translation_mode"], "text")
        self.assertEqual(list(payload["languages"]), self.codes)
        self.assertEqual([term["lang"] for term in payload["terms"]], self.codes)

    def test_a_view_lists_languages_in_sequence(self):
        """Translated term by term, with no ``terms`` to sort."""
        payload = self._payload(self.env.ref("base.view_partner_form"), "arch_db")
        self.assertEqual(payload["translation_mode"], "xml")
        self.assertEqual(list(payload["languages"]), self.codes)
        self.assertNotIn("terms", payload)

    def test_core_s_payload_is_otherwise_untouched(self):
        """Re-ordered, never rebuilt: each language keeps what core said of it."""
        payload = self._payload(self.env.ref("base.es"), "name")
        self.assertEqual(
            payload["languages"]["ca_ES"],
            {"name": "Catalan / Català", "direction": "ltr", "code": "ca_ES", "is_base": False},
        )
        self.assertTrue(payload["languages"]["en_US"]["is_base"])
        self.assertEqual(
            {term["lang"]: term["value"] for term in payload["terms"]}["en_US"], "Spain"
        )
