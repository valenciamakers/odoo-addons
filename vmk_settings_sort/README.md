# Settings Sort (`vmk_settings_sort`)

Two lists inside the Settings app arrive in an order nobody chose. This module sorts both.

**The settings sidebar**, down the left of the Settings screen, with **General Settings** kept at
the top. **The groupings in the Technical menu** — Actions, Database Structure, Email, Security and
the rest — leaving everything inside each grouping exactly as its author arranged it.

```
Technical, before: Discuss, Activities, Email, Phone / SMS, Actions, IAP, User Interface, …
Technical, after:  Actions, Activities, Automation, Calendar, Database Structure, Discuss, …
```

Both orders follow the user's own language, and neither writes anything: the sorting happens on the
way out, so nothing is left behind if the module is removed.

## The settings sidebar

The sidebar is drawn in arch order. `settings_form_compiler.js` walks `{selector: "app"}` in
document order, and `settings_page.js` sorts nothing at all. Each module contributes its section
with `<xpath expr="//form" position="inside">`, so the order you see is the order the inheriting
views happened to be applied in — and **General Settings is only first because `base_setup` sets its
view's `priority` to `0`**. Nothing marks it as the header, so this module pins it deliberately.

It is pinned by `name="general_settings"`, never by label: in Spanish the label is _Opciones
generales_, so a label match would unpin it for anyone not working in English.

`_get_view` is the override point, and sorting **after** `super()` is what makes it safe. The arch
is fully combined by then, so every third-party xpath has already matched — including
`sale_management` flipping `sale`'s block to `notApp="0"` — and reordering afterwards cannot break
any of them.

The labels are already translated at that point, `arch_db` being a translated field, so the order is
alphabetical in each user's own language for free. Verified rather than assumed:

```
en_US -> General Settings, CRM, Calendar, Website, Inventory
es_ES -> Opciones generales, CRM, Calendario, Sitio web, Inventario
```

One detail that matters in the implementation: `<form>` has children that are **not** `<app>`
blocks, `<field name="is_root_company" invisible="1"/>` among them. So each block is placed back
into a slot an `<app>` already occupied, rather than detached and re-appended, which would shuffle
those fields to the end.

## The Technical groupings

Their sequences collide in stock — three sit on `10`, two on `3`, two on `5`, two on `30` — so ties
break by `id`, which is install order. That is why the list looks arbitrary and why it differs
between databases.

Sorting happens in the `load_menus` payload, on the immediate children of `base.menu_custom`.
Targeting the **xmlid** is deliberate: `mail` ships a second menu also called "Technical", under
Discuss, and matching on the name would reorder that one too.

Only the immediate children are touched. What sits inside each grouping is a deliberate arrangement,
and alphabetising it would be a loss.

This part only ever applies in **developer mode**. Technical carries `groups="base.group_no_one"`,
so it is absent from the payload entirely otherwise, and the override hands it straight back
unchanged.

## Testing, and why it is shaped this way

Neither sort can be proved against live data:

- The live arch cannot show that a block landed in the **slot** it should have, only that the blocks
  came out in some order.
- The live menu payload cannot show the Technical ordering **at all**. `_filter_visible_menus` reads
  `request.session.debug` rather than the `debug` argument `load_menus` was given — that argument
  only feeds the ormcache key — so a `group_no_one` menu is filtered out of any payload fetched
  without an HTTP request, and a `TransactionCase` has none.

So both orderings are tested against fixtures built in the test file, where every element is known,
and the live checks confirm only that the overrides are wired in. The Technical path was then
verified by hand over an authenticated HTTP session in developer mode, which is the one way to
exercise it end to end.

```bash
odoo -d <db> -u vmk_settings_sort --test-enable --test-tags /vmk_settings_sort --stop-after-init
```

## Notes

- **`folded_label` is a third copy** of the same three lines carried by
  [`vmk_apps_menu_sort`](../vmk_apps_menu_sort). Sharing it would mean one module depending on the
  other purely for a string helper, coupling two features with nothing else in common. If you change
  the folding rule, change it in both.
- **This module and `vmk_apps_menu_sort` both override `load_menus`.** They rewrite different keys
  of the payload — root children versus Technical's children — and compose through the MRO. There is
  a test asserting the root ordering still holds with both installed.
- Sorting interleaves app names with functional groupings: _Database Structure_ lands between
  _Calendar_ and _Discuss_. That is the trade for a list you can scan.

## Requirements

Odoo 19. Depends on `base` only.
