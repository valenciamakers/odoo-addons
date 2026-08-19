# Copyright 2026 Valencia Makers, SL
# License AGPL-3 (https://www.gnu.org/licenses/agpl-3.0.html).

"""Sorting helpers shared by this module's two overrides.

`folded_label` is deliberately a third copy of the same three lines that
`vmk_apps_menu_sort` carries. Sharing it would mean one module depending on the
other purely for a string helper, coupling two features that have nothing else
to do with each other. If you change the folding rule, change it in both.
"""

import unicodedata

# The settings sidebar block that stays at the top, identified by its `name`
# rather than its label: the label is "Opciones generales" in Spanish, so
# matching on it would unpin the block for anyone not working in English.
GENERAL_SETTINGS = "general_settings"


def folded_label(label):
    """Case- and accent-insensitive sort key, so `Álbum` sorts beside `Alta`.

    A bare `sorted()` compares code points, parking every accented initial after
    `Z`. Not full locale collation, which would want PyICU or process-global
    `locale` state; Spanish `ñ` folds onto `n` rather than sorting after it.
    """
    decomposed = unicodedata.normalize("NFKD", label or "")
    return "".join(c for c in decomposed if not unicodedata.combining(c)).casefold()


def sorted_children(menus, menu_id):
    """Return a `load_menus` payload with one menu's children sorted by name.

    Kept a pure function of the dict, both because the caller's input is an
    ormcached structure shared between requests and must not be mutated, and
    because the live path cannot be exercised from a `TransactionCase`:
    `_filter_visible_menus` reads `request.session.debug`, so a developer-mode
    menu is absent from any payload fetched without an HTTP request.
    """
    entry = menus.get(menu_id)
    if not entry:
        return menus
    children = entry.get("children")
    if not children or len(children) < 2:
        return menus
    in_order = sorted(children, key=lambda mid: folded_label(menus[mid]["name"]))
    return {**menus, menu_id: {**entry, "children": in_order}}


def sort_app_blocks(form):
    """Reorder the `<app>` children of a settings `<form>`, in place.

    Each block is put back into a slot an `<app>` already occupied, rather than
    detached and re-appended, because `<form>` holds other children too --
    `<field name="is_root_company" invisible="1"/>` among them -- and appending
    would shuffle those to the end.
    """
    apps = form.findall("./app")
    if len(apps) < 2:
        return form

    def sort_key(app):
        if (app.get("name") or "") == GENERAL_SETTINGS:
            return (0, "")
        return (1, folded_label(app.get("string")))

    # `string` is what the sidebar displays: the compiler reads
    # `el.getAttribute("string")` in `settings_form_compiler.js`, while
    # `data-string` feeds something else.
    in_order = iter(sorted(apps, key=sort_key))
    app_nodes = set(apps)
    children = list(form)
    form[:] = [next(in_order) if child in app_nodes else child for child in children]
    return form
