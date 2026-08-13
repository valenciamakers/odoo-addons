# Copyright 2026 Valencia Makers, SL
# License MIT (https://opensource.org/licenses/MIT).

from lxml import etree

from odoo.tests.common import TransactionCase, tagged

EXPECTED_ORDER = "application desc, shortdesc"


@tagged("post_install", "-at_install")
class TestAppsPageSort(TransactionCase):
    """The module is two view attributes, so the tests check they arrive.

    Reading the processed arch back is the point: an inherit whose anchor stops
    matching is the failure mode here, and it is silent. The page simply carries
    on in its original order.
    """

    def _view_root(self, xmlid, view_type):
        view = self.env.ref(xmlid)
        arch = self.env["ir.module.module"].get_view(view.id, view_type)["arch"]
        return etree.fromstring(arch)

    def test_the_apps_kanban_carries_the_order(self):
        root = self._view_root("base.module_view_kanban", "kanban")
        self.assertEqual(root.get("default_order"), EXPECTED_ORDER)

    def test_the_apps_list_carries_the_order(self):
        root = self._view_root("base.module_tree", "list")
        self.assertEqual(root.get("default_order"), EXPECTED_ORDER)

    def test_the_order_is_valid_for_the_model(self):
        """A `default_order` naming a field that does not exist fails at runtime.

        The views are data, so nothing validates the string at install time; the
        first person to open the Apps page finds out instead.
        """
        modules = self.env["ir.module.module"].search([], order=EXPECTED_ORDER, limit=5)
        self.assertTrue(modules)

    def test_applications_sort_ahead_of_other_modules(self):
        """`application desc` is kept so clearing the Apps filter stays sensible."""
        modules = self.env["ir.module.module"].search([], order=EXPECTED_ORDER)
        applications = [i for i, module in enumerate(modules) if module.application]
        others = [i for i, module in enumerate(modules) if not module.application]
        self.assertTrue(applications and others, "expected both kinds installed")
        self.assertLess(max(applications), min(others))
