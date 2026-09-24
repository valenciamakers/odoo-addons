# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from pathlib import Path
from unittest.mock import patch

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
class TestAlphabeticalOrder(TransactionCase):
    """The names sort as a person reads them, not in the database's byte order."""

    NAMES = {
        "vmk_test_crm": "Zz CRM",
        "vmk_test_calendar": "Zz Calendar",
        "vmk_test_contacts": "Zz Contacts",
        "vmk_test_exito": "Zz \u00c9xito",
        "vmk_test_exit": "Zz Exit",
        "vmk_test_zebra": "Zz Zebra",
    }

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Module = cls.env["ir.module.module"]
        for name, shortdesc in cls.NAMES.items():
            Module.create({"name": name, "shortdesc": shortdesc})

    def _ordered(self):
        modules = self.env["ir.module.module"].search(
            [("name", "in", list(self.NAMES))], order=EXPECTED_ORDER
        )
        return modules.mapped("shortdesc")

    def test_case_does_not_decide_the_order(self):
        """`CRM` sorts after `Calendar` and `Contacts`; byte order puts it first."""
        order = self._ordered()
        self.assertLess(order.index("Zz Calendar"), order.index("Zz Contacts"))
        self.assertLess(order.index("Zz Contacts"), order.index("Zz CRM"))

    def test_accented_names_sort_beside_their_letter(self):
        """With ICU, `\u00c9xito` sorts beside `Exit`, not after `Zebra`."""
        if not self.env["ir.module.module"]._vmk_name_collation():
            self.skipTest("this PostgreSQL has no ICU collation; lower() fixes case only")
        order = self._ordered()
        self.assertLess(order.index("Zz Exit"), order.index("Zz \u00c9xito"))
        self.assertLess(order.index("Zz \u00c9xito"), order.index("Zz Zebra"))

    def test_without_icu_case_still_does_not_decide(self):
        """A PostgreSQL built without ICU falls back to lower(): case is fixed, accents are not."""
        Module = type(self.env["ir.module.module"])
        with patch.object(Module, "_vmk_name_collation", return_value=None):
            order = self._ordered()
        self.assertLess(order.index("Zz Calendar"), order.index("Zz Contacts"))
        self.assertLess(order.index("Zz Contacts"), order.index("Zz CRM"))

    def test_descending_reverses_it(self):
        modules = self.env["ir.module.module"].search(
            [("name", "in", list(self.NAMES))], order="shortdesc desc"
        )
        self.assertEqual(modules.mapped("shortdesc"), list(reversed(self._ordered())))

    def test_other_fields_keep_core_ordering(self):
        """Only `shortdesc` is touched; ordering by the technical name is unchanged."""
        modules = self.env["ir.module.module"].search(
            [("name", "in", list(self.NAMES))], order="name"
        )
        self.assertEqual(modules.mapped("name"), sorted(self.NAMES))


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
        "Alphabetical order on the Apps page, sorted by the name shown on the card",
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
