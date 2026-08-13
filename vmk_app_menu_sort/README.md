# App Menu Sort (`vmk_app_menu_sort`)

Odoo lists the apps on the main menu in whatever order their `sequence` values happen to give, which
is a number each app's own module picked for itself. This module sorts them alphabetically instead,
keeping **Apps** and **Settings** at the end where Odoo conventionally puts them.

Verified on a database with six apps installed:

```
stock  : Discuss, Calendar, Contacts, CRM, Website, Inventory, Apps, Settings
sorted : Calendar, Contacts, CRM, Discuss, Inventory, Website, Apps, Settings
```

## Where the order applies

| Surface                                   | Edition    | Path                          |
| ----------------------------------------- | ---------- | ----------------------------- |
| The app grid on `/odoo`                   | Enterprise | `home_menu_service.js`        |
| The apps dropdown in the navbar           | both       | `menu_service.js` `getApps()` |
| The command palette, before you type      | both       | `menu_providers.js`           |
| "Go to your Odoo Apps" on the public site | both       | `website_templates.xml`       |

Everything in that list consumes a server payload verbatim — none of it sorts — so ordering the
payload reaches all of it at once.

## Why it sorts the payload, not the `sequence` values

The obvious implementation writes new `sequence` values onto the root menus. It would not survive.

Every app's root menu is shipped as module data by that app's own module, so `-u sale` rewrites
Sales' sequence, and `-u all` rewrites nearly all of them. Keeping written values would mean
freezing each record's `ir.model.data` row against updates, which is what `vmk_language_freeze_meta`
exists to do — a lot of machinery, and it would stop those records receiving genuine Odoo
corrections too.

Sorting the payload on the way out is stateless. Nothing is written, so there is nothing for a
module update to undo, and **Settings → Technical → User Interface → Menu Items** keeps showing true
stored sequence rather than a fiction this module maintains.

## Two payloads, not one

There are two independent code paths producing an app list, cached separately, and both need the
override:

| Method            | Consumer                                    | Entry shape                       |
| ----------------- | ------------------------------------------- | --------------------------------- |
| `load_menus`      | the whole backend web client                | ids, resolved against `menus[id]` |
| `load_menus_root` | `website`'s "Go to your Odoo Apps" dropdown | dicts from `read()`               |

`load_menus_root` is easy to miss: it never passes through `load_menus`, and its only consumer is a
QWeb `t-foreach` in `website_templates.xml` that renders it server-side for internal users browsing
the public site.

The two carry different data, which is why the pinned menus are identified by resolving `env.ref`
rather than by reading the payload. `load_menus` entries include an `xmlid` key and could be matched
directly; `load_menus_root` entries come from `read()` and carry no xmlid at all. One mechanism that
works on both beats two that each work on one.

## Why the result is copied rather than sorted in place

`ir.ui.menu.load_menus` is `@ormcache('self.env.uid', 'debug', 'self.env.lang')`, so the dict
`super()` returns is shared between requests. Sorting `root['children']` in place would appear to
work — sorting an already-sorted list is idempotent — while writing into a live cache entry that
other overrides also read. Core itself treats that return value as immutable: `load_web_menus`
builds a fresh dict and only ever reads from the cached one. The override does the same, at the cost
of a shallow copy per menu load.

No cache invalidation of our own is needed. `ir.ui.menu`'s `create`, `write`, and `unlink` each call
a bare `registry.clear_cache()`, which clears the `'default'` group — where all three menu-loading
caches live, none of them having passed an explicit `cache=` to `ormcache`.

## Pinning Apps and Settings

Nothing in Odoo marks those two as special. They carry `sequence="500"` and `"550"` in
`base/views/base_menus.xml`, purely by convention, and `base.menu_tests` sits above both on `1000` —
so there is no ceiling to inherit and "at the end" has to be asserted here.

They are ranked by their **position in `PINNED_LAST`**, never by name. Apps precedes Settings in
English, but in Spanish the names are _Aplicaciones_ and _Ajustes_, which sort the other way.
Ranking by name would swap the pair when a user changed language.

## Sorting and language

The payload is built per user language and cached per language, so each user gets the order that is
alphabetical **in their own language**. That is the intended behaviour, not a wrinkle: two users on
one database will legitimately see different orders.

Names are folded before comparison — NFKD-decomposed, combining marks dropped, then case-folded — so
`Ángulo` sorts beside `Anzuelo` instead of after `Zoo`, and a lowercase name does not sort after
every capitalised one. It is deliberately **not** full locale collation: that wants PyICU, or
process-global `locale` state which has no business in a threaded Odoo worker. The visible
consequence is that Spanish `ñ` folds onto `n` rather than sorting after it. The displayed name is
never modified; folding affects the sort key only.

## Interaction with the Enterprise app grid

Dragging an icon on the Enterprise app grid stores that user's own order in `homemenu_config` on
`res.users.settings`, and `home_menu_service.js` applies it over ours:

```js
const homemenuConfig = JSON.parse(user.settings?.homemenu_config || "null");
if (homemenuConfig) {
  reorderApps(apps, homemenuConfig);
}
```

The reorder happens **only** when something is stored, so any user who has never dragged an app sees
this module's order immediately. A user who has dragged one keeps their own order until it is
cleared — including, per `reorderApps`, having newly installed apps appear at the _front_ of their
grid, since apps missing from the stored list sort ahead of the ones named in it.

To hand everyone the module's order back, run the **Reset per-user app grid order** server action
(Settings → Technical → Actions → Server Actions, developer mode). From a shell:

```python
env["res.users.settings"].reset_app_grid_order()
env.cr.commit()
```

This module deliberately does **not** do that on install. `homemenu_config` is a user preference,
and deleting it as a silent side effect of installing a module is not acceptable behaviour in
something published. Users remain free to drag their own order back afterwards; the module sets the
baseline, not the last word.

Suppressing drag-to-reorder altogether would mean overriding Enterprise JavaScript, which would
require depending on `web_enterprise` and would put distribution of this module under the OEEL
rather than MIT. Not worth it for a cosmetic edge case.

## The landing screen

On **Community**, reordering the apps changes where users land after login. `action_service.js`
falls back to the user's Home Action (`res.users.action_id`) and, when that is unset — the default,
since it is opt-in per user — `webclient.js` `_loadDefaultApp()` selects `root.children[0]`, the
literal first app in this payload.

On **Enterprise** it does not. `web_enterprise` overrides `_loadDefaultApp()` to open the app grid,
so `root.children[0]` is never consulted.

If a fixed landing screen matters, set **Home Action** on the user. It takes priority over the
fallback and is independent of this module.

## Known limitations

- **Menus inside an app are untouched.** Their order is deliberate and semantic — Sales runs Orders
  → To Invoice → Products → Reporting → Configuration, roughly workflow order — and alphabetising it
  would put Configuration first. Only root menus are sorted.
- **The Menu Items list still shows stored sequence order.** It reads the database through the
  model's `_order`, not this payload. That is intentional; see above.
- **The command palette re-ranks once you type.** With an empty query it shows this module's order;
  as soon as there is a search term, `fuzzyLookup` ranks by text relevance instead.
- **Users with a stored grid order keep it** until the reset action is run.

## Requirements

Odoo 19. Depends on `base` only. Both overridden methods are defined there, and `res.users.settings`
is a `base` model too — the Enterprise-only `homemenu_config` field is detected at runtime, so the
reset action degrades to a no-op on Community rather than needing a dependency.

## Testing

```bash
odoo -d <db> -u vmk_app_menu_sort --test-enable --test-tags /vmk_app_menu_sort --stop-after-init
```

The tests assert relative order rather than a fixed list of apps, so they hold on any database. The
reset-action test covers whichever branch the database supports: the Community no-op, or the real
clearing path on Enterprise, rolled back with the test transaction.
