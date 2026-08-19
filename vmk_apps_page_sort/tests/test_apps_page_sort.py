# Copyright 2026 Valencia Makers, SL
# License AGPL-3 (https://www.gnu.org/licenses/agpl-3.0.html).

from pathlib import Path

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


@tagged("post_install", "-at_install")
class TestModuleNameTranslation(TransactionCase):
    """Guard the two catalogue entries `i18n export` will never regenerate.

    The module's own name and summary live on `ir.module.module` records whose
    `ir.model.data` row belongs to **base** (`ir_module.py` creates them as
    `base.module_<name>`), so the exporter attributes them to base and omits
    them from our POT. They are in `i18n/` by hand -- the module's own view
    attributes generate no translatable terms at all, so this catalogue exists
    for nothing else.

    That matters because `PoFileReader` merges each PO against its module's
    POT and skips anything the merge marks obsolete -- so an entry missing
    from the POT is discarded in silence, translations and all. Re-running
    `i18n export` overwrites the POT and would do exactly that. This test is
    what turns that into a failure instead of a quiet regression.
    """

    I18N = Path(__file__).resolve().parent.parent / "i18n"
    HAND_MAINTAINED = (
        "Apps Page Sort",
        "Order the Apps page by the name on the card, not the hidden technical name",
    )

    def test_pot_still_carries_the_hand_added_module_metadata(self):
        pot = (self.I18N / "vmk_apps_page_sort.pot").read_text(encoding="utf-8")
        for msgid in self.HAND_MAINTAINED:
            with self.subTest(msgid=msgid):
                self.assertIn(
                    f'msgid "{msgid}"',
                    pot,
                    "The POT has lost an entry `odoo i18n export` does not generate. If you "
                    "just re-exported it, re-add the two `base.module_vmk_apps_page_sort` "
                    "blocks by hand -- without them the module name and summary silently stop "
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
        exporter would start emitting them and the hand-maintenance above
        becomes not just unnecessary but actively wrong.
        """
        data = self.env["ir.model.data"].search(
            [("model", "=", "ir.module.module"), ("name", "=", "module_vmk_apps_page_sort")]
        )
        self.assertEqual(data.module, "base")
