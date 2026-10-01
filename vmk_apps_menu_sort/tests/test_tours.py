# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

import json

from odoo.addons.vmk_apps_menu_sort.models.ir_ui_menu import PINNED_LAST
from odoo.tests.common import HttpCase, tagged

# The apps the tours look at, in the order their `sequence` gives them, which
# is not the alphabetical one: an accent and a lowercase initial both sort
# wrongly by code point. In Spanish, Mango becomes Abeto and moves to the front.
FIXTURE_APPS = ("Zebra Crossing", "ángulo recto", "Mango", "apple")
SPANISH = {"Mango": "Abeto"}


@tagged("post_install", "-at_install")
class TestTours(HttpCase):
    """Drive the apps list in a real browser, where the order is decided last.

    The tours read what the user sees. Which apps a database has depends on
    what is installed, so the tests add four of their own and the tours work
    out the expected order from the names on screen.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.enterprise = bool(
            cls.env["ir.module.module"].search_count(
                [("name", "=", "web_enterprise"), ("state", "=", "installed")]
            )
        )
        cls.admin = cls.env.ref("base.user_admin")
        cls.admin.lang = "en_US"
        cls.env["res.lang"]._activate_lang("es_ES")
        # Core drops a root menu with neither an action nor visible children.
        action = cls.env.ref("base.action_res_users")
        cls.apps = cls.env["ir.ui.menu"].create(
            [
                {
                    "name": name,
                    "parent_id": False,
                    "sequence": sequence,
                    "action": f"ir.actions.act_window,{action.id}",
                }
                for sequence, name in enumerate(FIXTURE_APPS, start=1)
            ]
        )
        # The client tells apps apart by xmlid.
        cls.env["ir.model.data"].create(
            [
                {
                    "module": "vmk_apps_menu_sort",
                    "name": f"test_tour_app_{position}",
                    "model": "ir.ui.menu",
                    "res_id": app.id,
                }
                for position, app in enumerate(cls.apps)
            ]
        )
        cls.app_xmlids = [
            f"vmk_apps_menu_sort.test_tour_app_{position}" for position in range(len(cls.apps))
        ]
        for app in cls.apps:
            if app.name in SPANISH:
                app.with_context(lang="es_ES").name = SPANISH[app.name]
        # Whether or not core's Spanish is loaded: by name, Ajustes (Settings)
        # would come before Aplicaciones (Apps).
        for xmlid, name in zip(PINNED_LAST, ("Aplicaciones", "Ajustes")):
            cls.env.ref(xmlid).with_context(lang="es_ES").name = name

    def _settings(self):
        return self.env["res.users.settings"]._find_or_create_for_user(self.admin)

    def _shown_order(self, lang):
        menu = self.env["ir.ui.menu"].with_user(self.admin).with_context(lang=lang)
        menus = menu.load_menus(False)
        return [menus[menu_id]["xmlid"] for menu_id in menus["root"]["children"]]

    def test_the_fixture_is_not_already_in_order(self):
        """Without this the tours could pass for want of anything to sort."""
        by_sequence = [self.env["ir.ui.menu"]._app_name_sort_key(name) for name in FIXTURE_APPS]
        self.assertNotEqual(by_sequence, sorted(by_sequence))
        self.assertNotEqual(by_sequence, sorted(by_sequence, reverse=True))

    def test_home_menu_is_alphabetical_on_enterprise(self):
        if not self.enterprise:
            self.skipTest("The home menu is an Enterprise feature")
        self.start_tour("/odoo", "vmk_apps_menu_sort_home_menu", login="admin")

    def test_stored_grid_order_wins_and_reset_restores_ours(self):
        if not self.enterprise:
            self.skipTest("The home menu is an Enterprise feature")
        zebra, _angulo, mango, _apple = self.app_xmlids
        self._settings().homemenu_config = json.dumps([PINNED_LAST[1], zebra, mango])
        self.start_tour("/odoo", "vmk_apps_menu_sort_home_menu_stored_order", login="admin")
        # The control: running the reset action hands the module's order back.
        self.env["res.users.settings"].reset_app_grid_order()
        self.assertFalse(self._settings().homemenu_config)
        self.start_tour("/odoo", "vmk_apps_menu_sort_home_menu", login="admin")

    def test_navbar_dropdown_is_alphabetical_on_community(self):
        if self.enterprise:
            self.skipTest("Community only: Enterprise opens the home menu instead")
        self.start_tour("/odoo", "vmk_apps_menu_sort_navbar", login="admin")

    def test_bare_odoo_lands_on_the_first_app_on_community(self):
        if self.enterprise:
            self.skipTest("Community only: Enterprise opens the home menu instead")
        self.admin.action_id = False
        self.start_tour("/odoo", "vmk_apps_menu_sort_landing", login="admin")

    def test_order_follows_the_spanish_names(self):
        # The pair really differs: the apps come in another order in Spanish.
        self.assertNotEqual(self._shown_order("en_US"), self._shown_order("es_ES"))
        self.admin.lang = "es_ES"
        self.start_tour("/odoo", "vmk_apps_menu_sort_spanish", login="admin")
