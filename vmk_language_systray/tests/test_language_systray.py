# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

"""Almost all of this module is assets, and the JS leans entirely on core's
own behaviour: an unprivileged self-write on ``res.users.lang``, and
``res.lang.get_installed()``. The first class covers that server-side
contract rather than any code of ours, so an Odoo upgrade that changes either
one surfaces here instead of silently in the browser.

The second covers the one piece of Python the module does ship: the
``session_info`` key carrying the ``show_name`` flag.
"""

from pathlib import Path

from odoo.exceptions import AccessError
from odoo.tests import new_test_user
from odoo.tests.common import HttpCase, TransactionCase, tagged
from odoo.tools import mute_logger

from ..models.ir_http import SHOW_NAME_PARAM


@tagged("post_install", "-at_install")
class TestLanguageSystray(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ResLang = cls.env["res.lang"]
        # base.group_user, the default for new_test_user, is a plain
        # internal, non-admin user. It may write only fields marked
        # `user_writeable`, and only on its own record (`res.users._has_field_access`
        # and the `res_users_rule_write_self` rule in base/security/ir.access.csv).
        cls.staff = new_test_user(cls.env, login="vmk_systray_staff")

    def test_user_can_write_own_lang_alone(self):
        """The one write the JS ever issues: `lang`, and nothing else."""
        self.staff.with_user(self.staff).write({"lang": "en_US"})
        self.assertEqual(self.staff.lang, "en_US")

    def test_user_cannot_write_lang_together_with_other_field(self):
        """Why the JS must never add a key that is not `user_writeable`.

        Odoo 19 checked that every key was in `SELF_WRITEABLE_FIELDS`; 20 marks
        the field itself `user_writeable` and checks each key on its own. Either
        way `login` is not one, so pairing it with `lang` refuses the whole write.
        """
        with self.assertRaises(AccessError):
            self.staff.with_user(self.staff).write(
                {"lang": "en_US", "login": "renamed_login"}
            )

    def test_lang_is_a_user_writeable_field(self):
        """The premise of the JS write: it is the field's own flag, not a list."""
        self.assertTrue(self.env["res.users"]._fields["lang"].user_writeable)
        self.assertFalse(getattr(self.env["res.users"]._fields["login"], "user_writeable", False))

    def test_get_installed_covers_exactly_the_active_languages(self):
        """Activate a language inside the test rather than assuming one is
        active, so this fails if `get_installed()` ever stops matching
        `res.lang`'s own active set.
        """
        self.ResLang._activate_lang("fr_FR")
        installed_codes = {code for code, _name in self.ResLang.get_installed()}
        active_codes = set(
            self.ResLang.with_context(active_test=True).search([]).mapped("code")
        )
        self.assertEqual(installed_codes, active_codes)
        self.assertIn("fr_FR", installed_codes)

    def test_get_installed_pairs_are_code_and_name(self):
        lang = self.ResLang._activate_lang("fr_FR")
        installed = dict(self.ResLang.get_installed())
        self.assertEqual(installed[lang.code], lang.name)

    def test_name_trim_matches_the_js_split_and_trim(self):
        """Mirrors `name.split("/").pop().trim()` in language_systray.js.

        Driven off a real res.lang record rather than a literal, so a change
        to Odoo's own "English / Spanish / Español" naming convention shows
        up here instead of only in the browser.
        """
        lang = self.ResLang._activate_lang("es_ES")
        self.assertIn("/", lang.name, "test assumes es_ES keeps its '/' name")
        js_equivalent = lang.name.split("/")[-1].strip()
        self.assertFalse(js_equivalent.startswith(" "))
        self.assertFalse(js_equivalent.endswith(" "))
        self.assertTrue(js_equivalent)


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
        "Backend Language Menu",
        "Switch your own backend language from a dropdown in the menu bar",
    )

    def test_pot_still_carries_the_hand_added_module_metadata(self):
        pot = (self.I18N / "vmk_language_systray.pot").read_text(encoding="utf-8")
        for msgid in self.HAND_MAINTAINED:
            with self.subTest(msgid=msgid):
                self.assertIn(
                    f'msgid "{msgid}"',
                    pot,
                    "The POT has lost an entry for the module's name or summary. If you "
                    "just re-exported it, check the two `base.module_vmk_language_systray` "
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
            [("model", "=", "ir.module.module"), ("name", "=", "module_vmk_language_systray")]
        )
        self.assertEqual(data.module, "base")


@tagged("post_install", "-at_install")
class TestShowNameFlag(HttpCase):
    """The `show_name` flag has to survive the whole trip to the browser.

    Driven over real HTTP rather than by calling `session_info()` directly,
    because the override reads `request.session` through core's own
    implementation and there is no request in a `TransactionCase`. This also
    exercises the part that actually matters: that an ordinary user, who
    cannot read `ir.config_parameter` at all, still receives the value.
    """

    def _flag_for(self, login, password):
        self.authenticate(login, password)
        info = self.make_jsonrpc_request("/web/session/get_session_info", {})
        self.assertIn(
            SHOW_NAME_PARAM, info, "the flag must always be present, not only when enabled"
        )
        return info[SHOW_NAME_PARAM]

    def test_flag_defaults_to_off_and_is_a_real_boolean(self):
        """Unset means off, and the client gets `false`, not `""` or `None`.

        The JS coerces with `Boolean(...)`, but a string `"False"` reaching it
        would coerce to `true` -- so the parsing has to happen server-side and
        this asserts it did.
        """
        self.env["ir.config_parameter"].sudo().search(
            [("key", "=", SHOW_NAME_PARAM)]
        ).unlink()
        self.assertIs(self._flag_for("admin", "admin"), False)

    def test_flag_reads_free_text_the_way_a_human_would_type_it(self):
        """It is a System Parameters text box, so `true` and `1` must work."""
        Param = self.env["ir.config_parameter"].sudo()
        for written, expected in (
            ("True", True),
            ("true", True),
            ("1", True),
            ("False", False),
            ("0", False),
            ("", False),
        ):
            with self.subTest(written=written):
                Param.set_str(SHOW_NAME_PARAM, written)
                # An empty value is not a boolean; `get_bool` logs that and answers off.
                with mute_logger("odoo.addons.base.models.ir_config_parameter"):
                    self.assertIs(self._flag_for("admin", "admin"), expected)

    def test_ordinary_user_receives_the_flag_despite_the_acl(self):
        """The whole reason the value travels in `session_info` under sudo.

        `ir.config_parameter` is readable only by `base.group_system`, so a
        plain internal user reading it directly gets an AccessError -- asserted
        here so that a future ACL relaxation does not quietly make the sudo
        look unnecessary.
        """
        self.env["ir.config_parameter"].sudo().set_bool(SHOW_NAME_PARAM, True)
        staff = new_test_user(
            self.env, login="vmk_systray_reader", password="vmk_systray_reader"
        )
        with self.assertRaises(AccessError):
            self.env["ir.config_parameter"].with_user(staff).search([]).mapped("key")
        self.assertIs(self._flag_for(staff.login, "vmk_systray_reader"), True)
