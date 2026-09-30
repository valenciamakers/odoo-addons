# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from pathlib import Path
from unittest.mock import patch

import polib
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
    """Guard the catalogue entries carrying the module's own name and summary.

    The module's name and summary live on an `ir.module.module` record whose
    `ir.model.data` row belongs to **base** (`ir_module.py` creates them as
    `base.module_<name>`). Odoo 19's exporter attributed them to base and left
    them out of our POT, so they were kept there by hand. Odoo 20's exporter
    writes them itself (`TranslationModuleReader._export_translatable_records`
    selects the `base.module_<name>` row of each exported module), and
    `Manifest.get_translations` reads them back from the module's own PO files
    by their `#:` reference, so a catalogue lacking that reference leaves the
    name in English on a module that is not installed yet.

    `PoFileReader` still merges each PO against its module's POT and skips
    whatever the merge marks obsolete, so an entry missing from the POT is
    still discarded in silence once the module is installed. These tests keep
    the entries, and their references, from going missing unnoticed.
    """

    I18N = Path(__file__).resolve().parent.parent / "i18n"
    MODULE_METADATA = (
        "Apps Page Sort",
        "Alphabetical order on the Apps page, sorted by the name shown on the card",
    )

    REFERENCES = (
        "model:ir.module.module,shortdesc:base.module_vmk_apps_page_sort",
        "model:ir.module.module,summary:base.module_vmk_apps_page_sort",
    )

    def _entries(self, filename):
        """The entries by msgid: the exporter wraps long ones, so read them as a parser does."""
        return {e.msgid: e for e in polib.pofile(str(self.I18N / filename))}

    def test_pot_still_carries_the_module_metadata(self):
        entries = self._entries("vmk_apps_page_sort.pot")
        for msgid, reference in zip(self.MODULE_METADATA, self.REFERENCES):
            with self.subTest(msgid=msgid):
                self.assertIn(
                    msgid,
                    entries,
                    "The POT has lost the module's name or summary. Re-export it with "
                    "`odoo i18n export`, which writes them on Odoo 20, or the module name and "
                    "summary silently stop being translated. See the README's Translations "
                    "section.",
                )
                self.assertIn(reference, [o for o, _ in entries[msgid].occurrences])

    def test_every_catalogue_translates_them(self):
        for po_name in ("es.po", "ca.po"):
            entries = self._entries(po_name)
            for msgid, reference in zip(self.MODULE_METADATA, self.REFERENCES):
                with self.subTest(po=po_name, msgid=msgid):
                    self.assertIn(msgid, entries)
                    self.assertTrue(entries[msgid].msgstr, "untranslated")
                    self.assertIn(reference, [o for o, _ in entries[msgid].occurrences])

    def test_the_module_record_really_is_owned_by_base(self):
        """The premise the `#:` references encode: the xmlid is base's, not ours.

        The catalogues name the record `base.module_vmk_apps_page_sort`. If Odoo
        ever moved these records into the module's own namespace, every
        reference would stop matching.
        """
        data = self.env["ir.model.data"].search(
            [("model", "=", "ir.module.module"), ("name", "=", "module_vmk_apps_page_sort")]
        )
        self.assertEqual(data.module, "base")
