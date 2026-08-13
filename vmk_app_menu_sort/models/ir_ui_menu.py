# Copyright 2026 Valencia Makers, SL
# License MIT (https://opensource.org/licenses/MIT).

import unicodedata

from odoo import api, models

# Root menus held at the end of the app list, in this order whatever the user's
# language. Nothing in Odoo marks these two as special: they simply carry
# sequence 500 and 550 in `base/views/base_menus.xml`, and `base.menu_tests`
# sits above both on 1000 -- so "at the end" has to be asserted here rather than
# inherited from stock.
PINNED_LAST = (
    "base.menu_management",  # Apps
    "base.menu_administration",  # Settings
)


class IrUiMenu(models.Model):
    _inherit = "ir.ui.menu"

    @api.model
    def _app_name_sort_key(self, name):
        """Fold case and accents, so `Ángulo` sorts beside `Anzuelo`.

        A bare `sorted()` compares code points, which parks every accented
        initial after `Z`. This is deliberately not full locale collation --
        that wants PyICU, or process-global `locale` state which has no place in
        a threaded Odoo worker -- so Spanish `ñ` folds onto `n` instead of
        sorting after it. Sort key only; the displayed name is untouched.
        """
        decomposed = unicodedata.normalize("NFKD", name or "")
        return "".join(c for c in decomposed if not unicodedata.combining(c)).casefold()

    @api.model
    def _root_menu_sort_key(self):
        """Build the ranking applied to each root menu's `(id, name)`.

        The pinned ids are resolved once per payload rather than once per menu:
        `env.ref` is cheap, `_xmlid_lookup` being ormcached, but not free.
        """
        pinned = {}
        for position, xmlid in enumerate(PINNED_LAST):
            menu = self.env.ref(xmlid, raise_if_not_found=False)
            if menu:
                pinned[menu.id] = position

        def sort_key(menu_id, name):
            if menu_id in pinned:
                # Ranked by position in PINNED_LAST, never by name: Apps precedes
                # Settings in English but not in Spanish (Ajustes, Aplicaciones),
                # and the pair should not swap when a user changes language.
                return (1, pinned[menu_id], "")
            return (0, 0, self._app_name_sort_key(name))

        return sort_key

    @api.model
    def load_menus(self, debug):
        """Order the app list served to the web client.

        This payload backs `/web/webclient/load_menus`, and every backend app
        list is built from its `root.children` in the order given: the
        Enterprise app grid, the Community app dropdown, and the command
        palette. None of them sorts -- `menu_service.js`'s `getApps()` is a bare
        `.map()` over the array -- so ordering it here reaches all three.
        """
        menus = super().load_menus(debug)
        root = menus.get("root")
        if not root or not root.get("children"):
            return menus
        sort_key = self._root_menu_sort_key()
        children = sorted(
            root["children"],
            key=lambda menu_id: sort_key(menu_id, menus[menu_id]["name"]),
        )
        # Shallow copies rather than sorting in place. `super()` is ormcached, so
        # its return value is shared between requests, and core treats it as
        # immutable -- `load_web_menus` builds a fresh dict and only ever reads
        # from this one. Sorting an already-sorted list in place would look
        # harmless while writing into a live cache entry other overrides read.
        return {**menus, "root": {**root, "children": children}}

    @api.model
    def load_menus_root(self):
        """Order the second app list, which is a separate code path entirely.

        `website` renders this one server-side in the "Go to your Odoo Apps"
        dropdown shown to internal users browsing the public site
        (`website_templates.xml`), through a `t-foreach` that applies no sort of
        its own. It never passes through `load_menus`, and it is cached
        separately, so consistency needs both overrides.
        """
        root = super().load_menus_root()
        children = root.get("children")
        if not children:
            return root
        sort_key = self._root_menu_sort_key()
        # These entries come from `read()` and carry no `xmlid`, unlike the ones
        # in `load_menus` -- which is why the pinned menus are identified by id
        # through `env.ref` rather than by the xmlid the other payload supplies.
        return {
            **root,
            "children": sorted(
                children, key=lambda menu: sort_key(menu["id"], menu["name"])
            ),
        }
