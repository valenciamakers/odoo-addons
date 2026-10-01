# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo.tests import HttpCase, tagged

# The sections the tours look at, in the order their view adds them, which is
# not the alphabetical one: an accent and a lowercase initial both sort wrongly
# by code point. In Spanish, Mango becomes Abeto and moves to the front.
FIXTURE_APPS = ("Zebra Crossing", "ángulo recto", "Mango", "apple")
SPANISH = {"Mango": "Abeto"}


@tagged("post_install", "-at_install")
class TestTours(HttpCase):
    """Drive the Settings screen and the Technical menu in a real browser.

    Which sections Settings has depends on what is installed, so the tests add
    four of their own, and the tours read the order off the screen and compare
    it with the promise.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin = cls.env.ref("base.user_admin")
        cls.admin.lang = "en_US"
        cls.env["res.lang"]._activate_lang("es_ES")
        apps = "".join(
            f"""<app string="{name}" name="vmk_settings_sort_test_{position}">
                    <block title="{name}">
                        <setting string="Company"><field name="company_id"/></setting>
                    </block>
                </app>"""
            for position, name in enumerate(FIXTURE_APPS)
        )
        cls.view = cls.env["ir.ui.view"].create(
            {
                "name": "vmk_settings_sort tour fixture",
                "model": "res.config.settings",
                "inherit_id": cls.env.ref("base.res_config_settings_view_form").id,
                "arch": f'<xpath expr="//form" position="inside">{apps}</xpath>',
            }
        )
        cls.view.update_field_translations("arch_db", {"es_ES": SPANISH})

    def _app_labels(self, lang):
        """The labels of the fixture's sections, in the order `lang` draws them."""
        arch, _view = (
            self.env["res.config.settings"].with_context(lang=lang)._get_view(view_type="form")
        )
        return [
            app.get("string")
            for app in arch.findall("./app")
            if app.get("name").startswith("vmk_settings_sort_test_")
        ]

    def test_the_fixture_is_sorted_and_differs_by_language(self):
        """Without this the tours could pass for want of anything to sort."""
        self.assertEqual(
            self._app_labels("en_US"), ["ángulo recto", "apple", "Mango", "Zebra Crossing"]
        )
        self.assertEqual(
            self._app_labels("es_ES"), ["Abeto", "ángulo recto", "apple", "Zebra Crossing"]
        )

    def test_sidebar_is_alphabetical(self):
        self.start_tour("/odoo/settings", "vmk_settings_sort_sidebar", login="admin")

    def test_technical_groupings_are_alphabetical_in_developer_mode(self):
        self.start_tour("/odoo/settings?debug=1", "vmk_settings_sort_technical", login="admin")

    def test_no_technical_menu_outside_developer_mode(self):
        self.start_tour("/odoo/settings", "vmk_settings_sort_no_technical", login="admin")

    def test_sidebar_follows_the_users_language(self):
        self.admin.lang = "es_ES"
        self.start_tour("/odoo/settings", "vmk_settings_sort_sidebar_translated", login="admin")
