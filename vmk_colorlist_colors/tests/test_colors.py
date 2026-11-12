# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

import re

from odoo.exceptions import AccessError, ValidationError
from odoo.tests.common import HttpCase, TransactionCase, new_test_user, tagged

from odoo.addons.vmk_colorlist_colors import _uninstall_hook
from odoo.addons.vmk_colorlist_colors.models import palette
from odoo.addons.vmk_colorlist_colors.models.vmk_colorlist_color import DARK_URL, LIGHT_URL


class ColorsCase(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        for lang in ("es_ES", "ca_ES"):
            cls.env["res.lang"]._activate_lang(lang)
        cls.Color = cls.env["vmk.colorlist.color"]
        # Whatever this database has set, the tests start from Odoo's colors.
        cls.Color.search([]).action_reset()
        cls.purple = cls.env.ref("vmk_colorlist_colors.color_5")
        cls.none = cls.env.ref("vmk_colorlist_colors.color_0")

    def _attachments(self):
        return self.env["ir.attachment"].search([("url", "in", [LIGHT_URL, DARK_URL])])

    def _assets(self):
        return self.env["ir.asset"].search([("path", "in", [LIGHT_URL, DARK_URL])])

    def _scss(self, url):
        return self._attachments().filtered(lambda a: a.url == url).raw.decode()


@tagged("post_install", "-at_install")
class TestColors(ColorsCase):

    def test_twelve_slots_with_odoos_values(self):
        colors = self.Color.search([])
        self.assertEqual(colors.mapped("slot"), list(range(12)))
        self.assertEqual(tuple(colors.mapped("color")), palette.COLORS)
        self.assertEqual(tuple(colors.mapped("odoo_name")), palette.NAMES)
        self.assertEqual(tuple(colors.mapped("name")), palette.NAMES)
        self.assertEqual(tuple(colors.mapped("display_name")), palette.NAMES)
        self.assertFalse(any(colors.mapped("is_custom")))

    def test_odoos_names_in_every_active_language(self):
        """A reset writes Odoo's name in every active language, as Odoo
        translates it."""
        self.assertEqual(self.purple.with_context(lang="es_ES").name, "Morado")
        self.assertEqual(self.purple.with_context(lang="ca_ES").name, "Morat")
        self.assertFalse(self.purple.with_context(lang="es_ES").is_custom)

    def test_odoos_names_in_the_users_language(self):
        """Odoo's names are JavaScript terms of web, read from web's own
        catalogue rather than from ours."""
        self.assertEqual(self.purple.with_context(lang="es_ES").odoo_name, "Morado")
        self.assertEqual(self.purple.with_context(lang="ca_ES").odoo_name, "Morat")

    def test_a_chosen_color_is_kept_in_lower_case(self):
        self.purple.color = "#7B2CBF"
        self.assertEqual(self.purple.custom_color, "#7b2cbf")
        self.purple.invalidate_recordset(["color"])
        self.assertEqual(self.purple.color, "#7b2cbf")
        self.assertTrue(self.purple.is_custom)

    def test_choosing_odoos_color_again_removes_the_custom_one(self):
        self.purple.color = "#7b2cbf"
        self.purple.color = palette.COLORS[5]
        self.assertFalse(self.purple.custom_color)
        self.assertFalse(self.purple.is_custom)

    def test_a_color_must_be_a_color(self):
        with self.assertRaises(ValidationError):
            self.purple.custom_color = "purple"

    def test_no_color_keeps_its_name(self):
        with self.assertRaises(ValidationError):
            self.none.name = "Ours"
        self.none.color = "#cccccc"
        self.assertEqual(self.none.custom_color, "#cccccc")

    def test_a_name_replaces_odoos(self):
        self.purple.name = "Brand"
        self.assertEqual(self.purple.display_name, "Brand")
        self.assertTrue(self.purple.is_custom)

    def test_names_come_translated_from_our_catalogues(self):
        """Loading a language gives each color its name in it, from our own
        catalogues, which carry core's translations of the names."""
        self.purple.update_field_translations("name", {"es_ES": False})
        self.env["ir.module.module"]._load_module_terms(
            ["vmk_colorlist_colors"], ["es_ES"], overwrite=True
        )
        self.purple.invalidate_recordset(["name"])
        self.assertEqual(self.purple.with_context(lang="es_ES").name, "Morado")

    def test_typing_odoos_name_again_is_not_custom(self):
        self.purple.name = "Brand"
        self.purple.name = "Purple"
        self.assertFalse(self.purple.is_custom)

    def test_reset_puts_back_odoos_color_and_name(self):
        self.purple.write({"color": "#7b2cbf", "name": "Brand"})
        self.purple.with_context(lang="es_ES").name = "Marca"
        action = self.purple.action_reset()
        self.assertEqual(action["tag"], "reload")
        self.assertFalse(self.purple.custom_color)
        self.assertEqual(self.purple.name, "Purple")
        self.assertEqual(self.purple.with_context(lang="es_ES").name, "Morado")
        self.assertFalse(self.purple.is_custom)

    def test_reset_all(self):
        self.purple.color = "#7b2cbf"
        self.env.ref("vmk_colorlist_colors.color_1").name = "Brick"
        self.Color.action_reset_all()
        self.assertFalse(any(self.Color.search([]).mapped("is_custom")))
        self.assertFalse(self._assets())

    def test_only_settings_users_reach_the_colors(self):
        user = new_test_user(self.env, login="vmk_colors_user", groups="base.group_user")
        with self.assertRaises(AccessError):
            self.purple.with_user(user).read(["color"])
        admin = new_test_user(self.env, login="vmk_colors_admin", groups="base.group_system")
        self.purple.with_user(admin).color = "#7b2cbf"
        self.assertEqual(self.purple.custom_color, "#7b2cbf")
        with self.assertRaises(AccessError):
            self.Color.with_user(admin).create({"slot": 12, "name": "Extra"})
        with self.assertRaises(AccessError):
            self.purple.with_user(admin).unlink()


@tagged("post_install", "-at_install")
class TestStylesheets(ColorsCase):

    def test_nothing_while_every_color_is_odoos(self):
        self.purple.name = "Brand"
        self.assertFalse(self._attachments())
        self.assertFalse(self._assets())

    def test_a_custom_color_puts_both_stylesheets_in_the_bundles(self):
        self.purple.color = "#7b2cbf"
        light, dark = (self._assets().filtered(lambda a, u=u: a.path == u) for u in (LIGHT_URL, DARK_URL))
        self.assertEqual(
            (light.bundle, light.directive),
            ("web._assets_primary_variables", "prepend"),
        )
        self.assertEqual(
            (dark.bundle, dark.directive, dark.target),
            ("web.dark_mode_variables", "before", LIGHT_URL),
        )
        self.assertEqual(len(self._attachments()), 2)

    def test_the_light_stylesheet(self):
        self.purple.color = "#7b2cbf"
        scss = self._scss(LIGHT_URL)
        shades = palette.shades("#7b2cbf")
        expected = {
            "o-colors": palette.COLORS[:5] + ("#7b2cbf",) + palette.COLORS[6:],
            "o-colors-border": palette.BORDER[:5] + (shades["border"],) + palette.BORDER[6:],
            "o-colors-bg-subtle": palette.BG_SUBTLE[:5] + (shades["bg_subtle"],) + palette.BG_SUBTLE[6:],
            "o-colors-text-emphasis": (
                palette.TEXT_EMPHASIS[:5] + (shades["text_emphasis"],) + palette.TEXT_EMPHASIS[6:]
            ),
        }
        for name, values in expected.items():
            with self.subTest(variable=name):
                line = re.search(rf"^\${name}: (.*) !default;$", scss, re.M)
                self.assertEqual(tuple(line.group(1).split(", ")), values)

    def test_the_dark_stylesheet(self):
        self.purple.color = "#7b2cbf"
        scss = self._scss(DARK_URL)
        self.assertRegex(scss, r"(?m)^\$o-colors: \(\);$")
        original = re.search(r"(?m)^\$o-colors-original: (.*);$", scss).group(1).split(", ")
        self.assertEqual(
            tuple(original), palette.DARK_COLORS[:5] + ("#7b2cbf",) + palette.DARK_COLORS[6:]
        )
        shade = palette.shades("#7b2cbf", dark=True)["bg_subtle"]
        bg = re.search(r"(?m)^\$o-colors-bg-subtle: (.*);$", scss).group(1).split(", ")
        self.assertEqual(bg[5], shade)

    def test_a_new_color_rewrites_the_stylesheets(self):
        self.purple.color = "#7b2cbf"
        self.purple.color = "#123456"
        self.assertIn("#123456", self._scss(LIGHT_URL))
        self.assertNotIn("#7b2cbf", self._scss(LIGHT_URL))
        self.assertEqual(len(self._assets()), 2)

    def test_the_last_custom_color_gone_removes_them(self):
        self.purple.color = "#7b2cbf"
        self.purple.action_reset()
        self.assertFalse(self._attachments())
        self.assertFalse(self._assets())

    def test_uninstalling_removes_them(self):
        self.purple.color = "#7b2cbf"
        _uninstall_hook(self.env)
        self.assertFalse(self._attachments())
        self.assertFalse(self._assets())

    def test_the_bundles_compile_with_the_color(self):
        """The stylesheets reach the compiled CSS, in the backend, on the
        website, and in Enterprise's dark mode where it is installed, which
        keeps twelve colors rather than appending to ours."""
        self.purple.color = "#7b2cbf"
        bundles = ["web.assets_web"]
        if self.env["ir.module.module"].search_count(
            [("name", "=", "web_enterprise"), ("state", "=", "installed")]
        ):
            bundles.append("web.assets_web_dark")
        for bundle in bundles:
            with self.subTest(bundle=bundle):
                css = self.env["ir.qweb"]._get_asset_bundle(bundle, css=True, js=False).css().raw
                css = css.decode()
                self.assertIn("o_colorlist_item_color_11", css)
                self.assertNotIn("o_colorlist_item_color_12", css)
                rule = re.search(r"\.o_colorlist_item_color_5\{[^}]*\}", css).group(0)
                expected = "RGBA(123, 44, 191," if bundle == "web.assets_web" else "RGBA(152."
                self.assertIn(expected, rule)


@tagged("post_install", "-at_install")
class TestSessionInfo(HttpCase):
    """The colors' names reach the web client in the user's language."""

    def test_names_in_the_session(self):
        for lang in ("es_ES", "ca_ES"):
            self.env["res.lang"]._activate_lang(lang)
        Color = self.env["vmk.colorlist.color"]
        Color.search([]).action_reset()
        purple = self.env.ref("vmk_colorlist_colors.color_5")
        purple.name = "Brand"
        purple.with_context(lang="es_ES").name = "Marca"

        self.authenticate("admin", "admin")
        names = self.make_jsonrpc_request("/web/session/get_session_info")["vmk_colorlist_names"]
        self.assertEqual(len(names), 12)
        self.assertEqual((names["1"], names["5"]), ("Red", "Brand"))

        self.env.ref("base.user_admin").lang = "es_ES"
        self.authenticate("admin", "admin")
        names = self.make_jsonrpc_request("/web/session/get_session_info")["vmk_colorlist_names"]
        self.assertEqual((names["1"], names["5"]), ("Rojo", "Marca"))

    def test_names_core_leaves_in_english(self):
        """Core's Catalan has no Almond or Teal; ours does, and the pickers
        show it."""
        self.env["res.lang"]._activate_lang("ca_ES")
        self.env["vmk.colorlist.color"].search([]).action_reset()
        self.env.ref("base.user_admin").lang = "ca_ES"
        self.authenticate("admin", "admin")
        names = self.make_jsonrpc_request("/web/session/get_session_info")["vmk_colorlist_names"]
        self.assertEqual((names["6"], names["7"]), ("Ametlla", "Verd blavós"))
