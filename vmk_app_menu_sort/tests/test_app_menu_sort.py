# Copyright 2026 Valencia Makers, SL
# License MIT (https://opensource.org/licenses/MIT).

from odoo.addons.vmk_app_menu_sort.models.ir_ui_menu import PINNED_LAST
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestAppMenuSort(TransactionCase):
    """Assertions are written against relative order, never a fixed app list.

    Which apps exist depends on what is installed, so every test here states a
    property that must hold on any database rather than naming the expected
    result.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Menu = cls.env["ir.ui.menu"]
        # Core drops a root menu with neither an action nor visible children
        # from the payload, so every menu created here is given one.
        cls.action = cls.env["ir.actions.act_window"].search([], limit=1)
        cls.pinned_ids = [cls.env.ref(xmlid).id for xmlid in PINNED_LAST]

    def _create_root_menu(self, name, sequence=100):
        return self.Menu.create(
            {
                "name": name,
                "parent_id": False,
                "sequence": sequence,
                "action": "ir.actions.act_window,%d" % self.action.id,
            }
        )

    def _payload(self):
        menus = self.Menu.load_menus(False)
        return menus["root"]["children"], menus

    def _unpinned_keys(self, children, name_of):
        return [
            self.Menu._app_name_sort_key(name_of(child))
            for child in children
            if self._id_of(child) not in self.pinned_ids
        ]

    @staticmethod
    def _id_of(child):
        """`load_menus` yields ids; `load_menus_root` yields dicts."""
        return child["id"] if isinstance(child, dict) else child

    def test_apps_are_listed_alphabetically(self):
        children, menus = self._payload()
        keys = self._unpinned_keys(children, lambda mid: menus[mid]["name"])
        self.assertEqual(keys, sorted(keys))

    def test_pinned_menus_come_last_in_declared_order(self):
        children, _menus = self._payload()
        expected = [mid for mid in self.pinned_ids if mid in children]
        self.assertTrue(expected, "expected Apps and/or Settings to be visible")
        self.assertEqual(children[-len(expected) :], expected)

    def test_pinned_menus_are_ranked_by_position_not_by_name(self):
        """Apps precedes Settings in English but not in Spanish.

        Renaming stands in for a language whose translations invert the pair,
        which is the case this module has to survive.
        """
        settings = self.env.ref("base.menu_administration")
        settings.name = "Aaa renamed settings"
        children, _menus = self._payload()
        self.assertEqual(children[-1], settings.id)

    def test_a_high_sequence_cannot_outrank_the_pinned_menus(self):
        """Nothing in stock Odoo caps `sequence`; `base.menu_tests` sits on 1000."""
        newcomer = self._create_root_menu("Zzz workshop", sequence=9999)
        children, _menus = self._payload()
        self.assertLess(
            children.index(newcomer.id), children.index(self.pinned_ids[0])
        )

    def test_accented_names_sort_beside_their_unaccented_neighbours(self):
        """Without folding, every accented initial lands after `Z`."""
        angulo = self._create_root_menu("Ángulo")
        anzuelo = self._create_root_menu("Anzuelo")
        azul = self._create_root_menu("Azul")
        children, _menus = self._payload()
        positions = [children.index(menu.id) for menu in (angulo, anzuelo, azul)]
        self.assertEqual(positions, sorted(positions))

    def test_sorting_ignores_case(self):
        """Comparing code points would put every capital ahead of every minuscule."""
        zebra = self._create_root_menu("zebra workshop")
        zoo = self._create_root_menu("Zoo workshop")
        children, _menus = self._payload()
        self.assertLess(children.index(zebra.id), children.index(zoo.id))

    def test_a_newly_created_app_lands_in_its_alphabetical_position(self):
        """Also covers invalidation: core clears the cache on menu create."""
        before, menus = self._payload()
        self._create_root_menu("Mmm workshop")
        after, menus = self._payload()
        self.assertEqual(len(after), len(before) + 1)
        keys = self._unpinned_keys(after, lambda mid: menus[mid]["name"])
        self.assertEqual(keys, sorted(keys))

    def test_no_menu_is_dropped_or_duplicated(self):
        children, menus = self._payload()
        self.assertEqual(len(children), len(set(children)))
        self.assertTrue(all(mid in menus for mid in children))

    def test_load_menus_root_is_sorted_too(self):
        """The website "Go to your Odoo Apps" dropdown reads this payload."""
        children = self.Menu.load_menus_root()["children"]
        keys = self._unpinned_keys(children, lambda menu: menu["name"])
        self.assertEqual(keys, sorted(keys))
        visible_pinned = [
            mid for mid in self.pinned_ids if mid in [m["id"] for m in children]
        ]
        self.assertEqual(
            [m["id"] for m in children][-len(visible_pinned) :], visible_pinned
        )

    def test_resetting_the_app_grid_order_reports_back(self):
        """Covers whichever branch the database supports.

        On Community `homemenu_config` does not exist and the method must say so
        rather than raise; on Enterprise this genuinely clears the stored orders,
        which the surrounding transaction then rolls back.
        """
        result = self.env["res.users.settings"].reset_app_grid_order()
        self.assertEqual(result["tag"], "display_notification")
        self.assertTrue(result["params"]["message"])

    def test_the_server_action_runs(self):
        """Exercises the `safe_eval` string in the data file end to end."""
        action = self.env.ref("vmk_app_menu_sort.action_reset_app_grid_order")
        self.assertEqual(action.run()["tag"], "display_notification")

    def test_the_server_action_offers_a_run_button(self):
        """Calling `run()` proves nothing about reaching it from the interface.

        The Run button in `view_server_action_form` carries
        `invisible="model_name != 'ir.actions.server' or state != 'code'"`, so an
        action bound to the model its code happens to touch has no way of being
        run by hand at all.
        """
        action = self.env.ref("vmk_app_menu_sort.action_reset_app_grid_order")
        self.assertEqual(action.state, "code")
        self.assertEqual(action.model_name, "ir.actions.server")

    def test_the_cached_payload_is_never_mutated(self):
        """`super()` is ormcached, so its return value is shared across requests."""
        first = self.Menu.load_menus(False)
        self.assertGreater(len(first["root"]["children"]), 1)
        first["root"]["children"].reverse()
        second = self.Menu.load_menus(False)
        self.assertNotEqual(
            first["root"]["children"], second["root"]["children"]
        )
