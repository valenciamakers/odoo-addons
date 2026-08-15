# Copyright 2026 Valencia Makers, SL
# License MIT (https://opensource.org/licenses/MIT).

"""Almost all of this module is assets, and the JS leans entirely on core's
own behaviour: an unprivileged self-write on ``res.users.lang``, and
``res.lang.get_installed()``. The first class covers that server-side
contract rather than any code of ours, so an Odoo upgrade that changes either
one surfaces here instead of silently in the browser.

The second covers the one piece of Python the module does ship: the
``session_info`` key carrying the ``show_name`` flag.
"""

from odoo.exceptions import AccessError
from odoo.tests import new_test_user
from odoo.tests.common import HttpCase, TransactionCase, tagged

from ..models.ir_http import SHOW_NAME_PARAM


@tagged("post_install", "-at_install")
class TestLanguageSystray(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ResLang = cls.env["res.lang"]
        # base.group_user, the default for new_test_user, is a plain
        # internal, non-admin user -- read-only on res.users
        # (base/security/ir.model.access.csv: access_res_users_employee is
        # 1,0,0,0), so any write only succeeds through the self-write path.
        cls.staff = new_test_user(cls.env, login="vmk_systray_staff")

    def test_user_can_write_own_lang_alone(self):
        """The one write the JS ever issues: `lang`, and nothing else."""
        self.staff.with_user(self.staff).write({"lang": "en_US"})
        self.assertEqual(self.staff.lang, "en_US")

    def test_user_cannot_write_lang_together_with_other_field(self):
        """Why the JS must never add a second key to that write call.

        `res.users.write()` only takes the sudo-free self-write path when
        *every* key in vals is in `SELF_WRITEABLE_FIELDS`. `login` is not on
        that list, so pairing it with `lang` falls through to needing
        ordinary write access on res.users, which this user does not have.
        """
        with self.assertRaises(AccessError):
            self.staff.with_user(self.staff).write(
                {"lang": "en_US", "login": "renamed_login"}
            )

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
                Param.set_param(SHOW_NAME_PARAM, written)
                self.assertIs(self._flag_for("admin", "admin"), expected)

    def test_ordinary_user_receives_the_flag_despite_the_acl(self):
        """The whole reason the value travels in `session_info` under sudo.

        `ir.config_parameter` is readable only by `base.group_system`, so a
        plain internal user reading it directly gets an AccessError -- asserted
        here so that a future ACL relaxation does not quietly make the sudo
        look unnecessary.
        """
        self.env["ir.config_parameter"].sudo().set_param(SHOW_NAME_PARAM, "True")
        staff = new_test_user(
            self.env, login="vmk_systray_reader", password="vmk_systray_reader"
        )
        with self.assertRaises(AccessError):
            self.env["ir.config_parameter"].with_user(staff).search([]).mapped("key")
        self.assertIs(self._flag_for(staff.login, "vmk_systray_reader"), True)
