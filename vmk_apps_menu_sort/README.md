# Apps Menu Sort (`vmk_apps_menu_sort`)

Alphabetical order for the apps menu, with Apps and Settings at the end. In standard Odoo, apps are
listed in whatever order they set for themselves, so the apps grid reads as no order at all. This
module lists them alphabetically, with **Apps** and **Settings** kept at the end.

**How to use it** is in the user documentation, [`doc/index.rst`](doc/index.rst), which the Odoo
Apps Store also shows on the module's page, together with the changelog.

It depends only on `base`. LGPL-3, © 2026 Valencia Makers, SL.

## For developers

Odoo lists the apps in the main menu in whatever order their `sequence` values happen to give, which
is a number each app's own module picked for itself. This module sorts them alphabetically instead,
keeping **Apps** and **Settings** at the end where Odoo conventionally puts them.

Checked on a database with six apps installed, before the browser tests below:

```
stock  : Discuss, Calendar, Contacts, CRM, Website, Inventory, Apps, Settings
sorted : Calendar, Contacts, CRM, Discuss, Inventory, Website, Apps, Settings
```

### Where the order applies

| Surface                                   | Edition    | Path                           |
| ----------------------------------------- | ---------- | ------------------------------ |
| The app grid on `/odoo`                   | Enterprise | `home_menu_service.js:39`      |
| The apps dropdown in the navbar           | both       | `menu_service.js:77` `getApps` |
| The command palette, before you type      | both       | `menu_providers.js:31`         |
| "Go to your Odoo Apps" on the public site | both       | `website_templates.xml:399`    |

Everything in that list consumes a server payload verbatim — none of it sorts — so ordering the
payload reaches all of it at once. (`getApps` is a `computed` over `root.children` in Odoo 20, still
a bare `.map()`; the paths above are Odoo 20's, in `web` and `web_enterprise`.)

### Why it sorts the payload, not the `sequence` values

The obvious implementation writes new `sequence` values onto the root menus. It would not survive.

Every app's root menu is shipped as module data by that app's own module, so `-u sale` rewrites
Sales' sequence, and `-u all` rewrites nearly all of them. Keeping written values would mean
freezing each record's `ir.model.data` row against updates, which is what
`vmk_language_protect_settings` exists to do — a lot of machinery, and it would stop those records
receiving genuine Odoo corrections too.

Sorting the payload on the way out is stateless. Nothing is written, so there is nothing for a
module update to undo, and **Settings → Technical → User Interface → Menu Items** keeps showing true
stored sequence rather than a fiction this module maintains.

### Two payloads, not one

There are two independent code paths producing an app list, cached separately, and both need the
override:

| Method            | Consumer                                    | Entry shape                       |
| ----------------- | ------------------------------------------- | --------------------------------- |
| `load_menus`      | the whole backend web client                | ids, resolved against `menus[id]` |
| `load_menus_root` | `website`'s "Go to your Odoo Apps" dropdown | dicts from `read()`               |

`load_menus_root` is easy to miss: it never passes through `load_menus`, and its only consumer is a
QWeb `t-foreach` in `website_templates.xml` that renders it server-side for internal users browsing
the public site.

The two carry different data, which is why the pinned menus are identified by resolving their xmlids
to ids with `_xmlid_to_res_id` rather than by reading the payload. `load_menus` entries include an
`xmlid` key and could be matched directly; `load_menus_root` entries come from `read()` and carry no
xmlid at all. One mechanism that works on both beats two that each work on one.

### Why the result is copied rather than sorted in place

`ir.ui.menu.load_menus` is `@api.ormcache('self.env.uid', 'debug', 'self.env.lang')`
(`odoo/addons/base/models/ir_ui_menu.py:229`), so the dict `super()` returns is shared between
requests. Sorting `root['children']` in place would appear to work — sorting an already-sorted list
is idempotent — while writing into a live cache entry that other overrides also read. Core itself
treats that return value as immutable: `load_web_menus` (`addons/web/models/ir_ui_menu.py:12`)
builds a fresh dict and only ever reads from the cached one. The override does the same, at the cost
of a shallow copy per menu load.

No cache invalidation of our own is needed. `ir.ui.menu` declares `_clear_cache_name = 'default'`
(`ir_ui_menu.py:21`), and the ORM's `create`, `write`, and `unlink` invalidate that named cache
(`odoo/orm/models.py:3797`, `:3984`, `:4226`) — the group where all three menu-loading caches live,
none of them having passed an explicit `cache=` to `ormcache`. Odoo 19 did the same with a bare
`registry.clear_cache()` in the menu model's own methods, which Odoo 20 removed along with the
method.

**The browser now keeps its own copy.** `menu_service.js:48-72` stores the payload in IndexedDB
(`webclient_menu`, keyed by `session.registry_hash`), paints from it at once, and refetches in the
background, replacing it and redrawing when it differs. So the first page load after this module is
installed, or after an upgrade changes the order, can still show the old order for a moment before
the fetch lands; `registry_hash` changing on an upgrade is what retires the stored copy. That is the
client-side twin of the view cache noted in `DEVELOPING.md`.

### Pinning Apps and Settings

Nothing in Odoo marks those two as special. They carry `sequence="500"` and `"550"` in
`base/views/base_menus.xml` (lines 7 and 37), purely by convention, and `base.menu_tests` sits above
both on `1000` (line 116; in Odoo 20 restricted to `group_user_regular`) — so there is no ceiling to
inherit and "at the end" has to be asserted here.

They are ranked by their **position in `PINNED_LAST`**, never by name. Apps precedes Settings in
English, but in Spanish the names are _Aplicaciones_ and _Ajustes_, which sort the other way.
Ranking by name would swap the pair when a user changed language.

### Sorting and language

The payload is built per user language and cached per language, so each user gets the order that is
alphabetical **in their own language**. That is the intended behaviour, not a wrinkle: two users on
one database will legitimately see different orders.

Names are folded before comparison — NFKD-decomposed, combining marks dropped, then case-folded — so
`Ángulo` sorts beside `Anzuelo` instead of after `Zoo`, and a lowercase name does not sort after
every capitalised one. It is deliberately **not** full locale collation: that wants PyICU, or
process-global `locale` state which has no business in a threaded Odoo worker. The visible
consequence is that Spanish `ñ` folds onto `n` rather than sorting after it. The displayed name is
never modified; folding affects the sort key only.

### Interaction with the Enterprise app grid

Dragging an icon in the Enterprise apps grid stores that user's own order in `homemenu_config` on
`res.users.settings`, and `home_menu_service.js` applies it over ours
(`web_enterprise/static/src/webclient/home_menu/home_menu_service.js:39-44`, `reorderApps` in
`web/static/src/webclient/menus/menu_helpers.js:72`); the field is
`web_enterprise/models/res_users_settings.py:10`:

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

To hand everyone the module's order back, run the **Reset per-user app grid order** server action:

1. Activate developer mode, under Settings → General Settings → Developer Tools. The Technical menu
   carries `groups="base.group_no_one"`, so it does not exist until you do.
2. Go to Settings → Technical → Actions → Server Actions, or straight to
   `/odoo/action-base.action_server_action`.
3. Open **Reset per-user app grid order** and click **Run** in the form header.

A notification reports how many users were reset. Anyone already logged in needs to reload the page,
their settings having come down with it.

The same thing from a shell, skipping developer mode entirely:

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
rather than LGPL-3. Not worth it for a cosmetic edge case.

### The landing screen

On **Community**, reordering the apps changes where users land after login. The action plugin falls
back to the user's Home Action (`res.users.action_id`, `action_plugin.js:652`) and, when that is
unset — the default, since it is opt-in per user — `webclient.js` `_loadDefaultApp()` (line 146)
selects `root.children[0]`, the literal first app in this payload.

On **Enterprise** it does not. `web_enterprise` overrides `_loadDefaultApp()` to open the app grid
(`webclient/webclient.js:14`), so `root.children[0]` is never consulted.

If a fixed landing screen matters, set **Home Action** on the user. It takes priority over the
fallback and is independent of this module.

### Known limitations

- **Menus inside an app are untouched.** Their order is deliberate and semantic — Sales runs Orders
  → To Invoice → Products → Reporting → Configuration, roughly workflow order — and alphabetising it
  would put Configuration first. Only root menus are sorted.
- **The Menu Items list still shows stored sequence order.** It reads the database through the
  model's `_order`, not this payload. That is intentional; see above.
- **The command palette re-ranks once you type.** With an empty query it shows this module's order;
  as soon as there is a search term, `fuzzyLookup` ranks by text relevance instead.
- **Users with a stored grid order keep it** until the reset action is run.

### Translations

The module's own name and summary in `i18n/vmk_apps_menu_sort.pot`, `es.po` and `ca.po` were
hand-maintained until Odoo 19, since `ir.module.module` records belong to `base`'s xmlid namespace
and the exporter never saw them. See
[`vmk_language_systray`'s README](../vmk_language_systray#the-modules-own-name-and-summary-in-i18n)
for the full explanation. Odoo 20's exporter emits both entries under this module's name, and also
dumps the whole README as the module's `description`, which the catalogues leave out.
`tests/test_apps_menu_sort.py::TestModuleNameTranslation` fails loudly if re-running the export
drops them.

**One term departs from core on purpose.** Core's Catalan for _User Settings_ is
`Arranjament d' usuari` — with a space after the apostrophe — in twelve modules including `base`.
This module writes `Arranjament d'usuari`. Taking core's wording is the rule here; taking its
typography is not. It is this module's one deliberate divergence from core's catalogues. Decided 22
September 2026.

### Browser tests

`tests/test_tours.py` drives the order in a real browser, since the web client decides it last. The
tests add four apps of their own, with an accent and a lowercase initial among them, so the result
does not depend on what is installed, and each tour works out the expected order from the names on
screen. Enterprise: the home menu is alphabetical with Apps and Settings last, a stored
`homemenu_config` wins over it, and the **Reset per-user app grid order** logic hands the module's
order back (the control). Community: the navbar dropdown is alphabetical, and a bare `/odoo` opens
its first app. Either edition: in Spanish the order follows the translated names, with Apps still
ahead of Settings. Each test skips itself on the edition it does not apply to. The tours ran
unchanged on Odoo 20 (1 October 2026): its home menu, navbar dropdown, and landing screen carry the
same selectors as 19's.

### Requirements

Odoo 20. Depends on `base` only. Both overridden methods are defined there, and `res.users.settings`
is a `base` model too — the Enterprise-only `homemenu_config` field is detected at runtime, so the
reset action degrades to a no-op on Community rather than needing a dependency.

### Testing

```bash
odoo -d <db> -u vmk_apps_menu_sort --test-enable --test-tags /vmk_apps_menu_sort --stop-after-init
```

The tests assert relative order rather than a fixed list of apps, so they hold on any database. The
reset-action test covers whichever branch the database supports: the Community no-op, or the real
clearing path on Enterprise, rolled back with the test transaction.

On Odoo 20 (30 September 2026) the tests pass on Community and on Enterprise, with core's
`TestPerfSessionInfo` alongside — it counts the queries `load_menus` makes on a cold cache, which is
why the pinned menus are resolved with `_xmlid_to_res_id` rather than `env.ref`. Verified against
`odoo:19` Community for the ordering itself, and on an Odoo 19 **Enterprise** instance on 2026-08-13
(not yet repeated on 20) for the two things Community cannot exercise: the app grid on `/odoo`
follows this module's order, and running the reset returned a grid whose owner had dragged icons
around back to it.
