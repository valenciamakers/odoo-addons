# Copyright 2026 Valencia Makers, SL
# License AGPL-3 (https://www.gnu.org/licenses/agpl-3.0.html).

from pathlib import Path

from lxml import etree

from odoo.addons.vmk_settings_sort.models.ir_ui_menu import TECHNICAL_MENU
from odoo.addons.vmk_settings_sort.models.sort_key import (
    folded_label,
    sort_app_blocks,
    sorted_children,
)
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSettingsSort(TransactionCase):
    """Both sorts are tested against structures built here.

    The live arch cannot show that a block landed in the slot it should have,
    and the live menu payload cannot show the Technical ordering at all:
    `_filter_visible_menus` reads `request.session.debug`, so a developer-mode
    menu is absent from any payload fetched without an HTTP request. Fixtures
    prove the ordering; the live checks confirm the overrides are wired in.
    """

    # --- the settings sidebar --------------------------------------------

    def test_blocks_are_reordered_into_the_slots_they_occupied(self):
        """Non-app children must not move: `<form>` holds `<field>` too."""
        form = etree.fromstring(
            """<form>
                 <field name="first"/>
                 <app name="zebra" string="Zebra"/>
                 <field name="second"/>
                 <app name="general_settings" string="General Settings"/>
                 <app name="alpha" string="Álpha"/>
               </form>"""
        )
        sort_app_blocks(form)
        self.assertEqual(
            [(child.tag, child.get("name")) for child in form],
            [
                ("field", "first"),
                ("app", "general_settings"),
                ("field", "second"),
                ("app", "alpha"),
                ("app", "zebra"),
            ],
        )

    def test_general_settings_is_pinned_by_name_not_by_label(self):
        """`General Settings` sorts after `Alpha`, so a label match would fail."""
        form = etree.fromstring(
            """<form>
                 <app name="alpha" string="Alpha"/>
                 <app name="general_settings" string="General Settings"/>
               </form>"""
        )
        sort_app_blocks(form)
        self.assertEqual(
            [child.get("name") for child in form], ["general_settings", "alpha"]
        )

    def test_hidden_blocks_are_kept(self):
        """`notApp="1"` blocks never render, but dropping one would break them."""
        form = etree.fromstring(
            """<form>
                 <app name="b" string="B"/>
                 <app name="hidden" string="A hidden" notApp="1"/>
               </form>"""
        )
        sort_app_blocks(form)
        self.assertEqual([child.get("name") for child in form], ["hidden", "b"])

    def test_a_single_block_is_left_alone(self):
        form = etree.fromstring('<form><app name="only" string="Only"/></form>')
        sort_app_blocks(form)
        self.assertEqual([child.get("name") for child in form], ["only"])

    def test_the_live_settings_sidebar_is_sorted(self):
        arch, _view = self.env["res.config.settings"]._get_view()
        apps = arch.findall("./app")
        self.assertGreater(len(apps), 1, "expected several settings blocks")
        self.assertEqual(apps[0].get("name"), "general_settings")
        keys = [folded_label(app.get("string")) for app in apps[1:]]
        self.assertEqual(keys, sorted(keys))

    # --- the Technical groupings -----------------------------------------

    def _payload(self):
        """A `load_menus`-shaped payload: entries by id, children as id lists."""
        return {
            "root": {"id": False, "name": "root", "children": [10]},
            10: {"id": 10, "name": "Technical", "children": [11, 12, 13]},
            11: {"id": 11, "name": "Zebra", "children": [21, 22]},
            12: {"id": 12, "name": "Álpha", "children": []},
            13: {"id": 13, "name": "database structure", "children": []},
            21: {"id": 21, "name": "Second", "children": []},
            22: {"id": 22, "name": "First", "children": []},
        }

    def test_groupings_sort_ignoring_case_and_accents(self):
        """Unfolded, `Álpha` would land after `Zebra` and so would the minuscule."""
        self.assertEqual(sorted_children(self._payload(), 10)[10]["children"], [12, 13, 11])

    def test_what_sits_inside_a_grouping_is_untouched(self):
        self.assertEqual(sorted_children(self._payload(), 10)[11]["children"], [21, 22])

    def test_the_payload_handed_in_is_never_mutated(self):
        """`load_menus` is ormcached, so its return value is shared."""
        menus = self._payload()
        sorted_children(menus, 10)
        self.assertEqual(menus[10]["children"], [11, 12, 13])

    def test_an_absent_menu_leaves_the_payload_alone(self):
        menus = self._payload()
        self.assertIs(sorted_children(menus, 999), menus)

    def test_a_lone_grouping_is_left_alone(self):
        menus = {10: {"children": [11]}, 11: {"name": "Only", "children": []}}
        self.assertIs(sorted_children(menus, 10), menus)

    def test_technical_is_absent_without_an_http_request(self):
        """Documents why the ordering above is tested against a fixture.

        `_filter_visible_menus` consults `request.session.debug`, and there is no
        request here, so a `group_no_one` menu is filtered out however
        `load_menus` is called. The override has to survive that, since it is
        also what every non-developer session sees.
        """
        menus = self.env["ir.ui.menu"].load_menus(True)
        technical = self.env.ref(TECHNICAL_MENU)
        self.assertNotIn(technical.id, menus)
        self.assertIn("root", menus)

    def test_it_composes_with_vmk_apps_menu_sort(self):
        """Both modules override `load_menus`, rewriting different keys."""
        installed = self.env["ir.module.module"].search(
            [("name", "=", "vmk_apps_menu_sort"), ("state", "=", "installed")]
        )
        if not installed:
            self.skipTest("vmk_apps_menu_sort is not installed")
        from odoo.addons.vmk_apps_menu_sort.models.ir_ui_menu import PINNED_LAST

        menus = self.env["ir.ui.menu"].load_menus(False)
        pinned = [self.env.ref(xmlid).id for xmlid in PINNED_LAST]
        keys = [
            folded_label(menus[child]["name"])
            for child in menus["root"]["children"]
            if child not in pinned
        ]
        self.assertEqual(keys, sorted(keys), "root menus lost their order")


@tagged("post_install", "-at_install")
class TestModuleNameTranslation(TransactionCase):
    """Guard the two catalogue entries `i18n export` will never regenerate.

    The module's own name and summary live on `ir.module.module` records whose
    `ir.model.data` row belongs to **base** (`ir_module.py` creates them as
    `base.module_<name>`), so the exporter attributes them to base and omits
    them from our POT. They are in `i18n/` by hand -- the module's own
    extracted terms (Config Settings, Display Name, ID, Menu) all belong to
    core and are deliberately left untranslated here, so this catalogue exists
    for nothing else.

    That matters because `PoFileReader` merges each PO against its module's
    POT and skips anything the merge marks obsolete -- so an entry missing
    from the POT is discarded in silence, translations and all. Re-running
    `i18n export` overwrites the POT and would do exactly that. This test is
    what turns that into a failure instead of a quiet regression.
    """

    I18N = Path(__file__).resolve().parent.parent / "i18n"
    HAND_MAINTAINED = (
        "Settings Sort",
        "Alphabetical order for the Settings sidebar and the Technical menu groupings",
    )

    def test_pot_still_carries_the_hand_added_module_metadata(self):
        pot = (self.I18N / "vmk_settings_sort.pot").read_text(encoding="utf-8")
        for msgid in self.HAND_MAINTAINED:
            with self.subTest(msgid=msgid):
                self.assertIn(
                    f'msgid "{msgid}"',
                    pot,
                    "The POT has lost an entry `odoo i18n export` does not generate. If you "
                    "just re-exported it, re-add the two `base.module_vmk_settings_sort` "
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
            [("model", "=", "ir.module.module"), ("name", "=", "module_vmk_settings_sort")]
        )
        self.assertEqual(data.module, "base")
