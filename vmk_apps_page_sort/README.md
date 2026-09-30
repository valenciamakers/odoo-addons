# Apps Page Sort (`vmk_apps_page_sort`)

Alphabetical order on the Apps page, sorted by the name shown on the card. In standard Odoo, the
Apps page is ordered by the hidden technical name of each app, so Employees is filed under _hr_ and
Invoicing under _account_. This module orders it by the name on the card, alphabetically.

**How to use it** is in the user documentation, [`doc/index.rst`](doc/index.rst), which the Odoo
Apps Store also shows on the module's page, together with the changelog.

It depends only on `base`. LGPL-3, © 2026 Valencia Makers, SL.

## For developers

The Apps page at `/odoo/apps` looks unsorted because it is ordered by a field it does not display.

`ir.module.module` declares `_order = 'application desc, sequence, name'`, where `name` is the
**technical** name — `hr`, `account`, `mail`. The card shows `shortdesc`, the module's display name,
which is also the model's `_rec_name`. So Employees files under `h`, Invoicing under `a`, and
Discuss under `m`, and the result reads as no order at all.

This module orders both Apps views by the name actually on the card.

### What it changes

Two view inherits, and one small override of how the name is compared:

| View                      | Used by                        |
| ------------------------- | ------------------------------ |
| `base.module_view_kanban` | the Apps page's default kanban |
| `base.module_tree`        | its list mode                  |

Both gain `default_order="application desc, shortdesc"`. Neither carries a `default_order` in stock,
so nothing is being overridden — the views simply fall back to the model's `_order` today. The names
are then compared alphabetically rather than in the database's byte order; see
[Sorting and language](#sorting-and-language).

`application desc` is kept deliberately. The Apps action passes `{'search_default_app': 1}`, so the
page is filtered to applications and the prefix changes nothing there; it earns its place when you
clear that filter, keeping applications ahead of the several hundred technical modules rather than
interleaving them.

What is given up is `sequence`, which Odoo uses to float particular modules to the top of the list.
A purely alphabetical page cannot also honour a curated order, and the curation is what makes the
page look arbitrary in the first place.

### Why the views rather than `_order`

Overriding `_order` on `ir.module.module` is one line and reaches every module list at once, which
is precisely the problem: that model is searched during install and upgrade paths, not only for
display. A `default_order` on the two views confines the change to the screens this module is about.

This is the same reasoning as [`vmk_apps_menu_sort`](../vmk_apps_menu_sort) sorting the menu payload
instead of writing `sequence` values — order the presentation, leave the data alone.

### Why both records anchor on the root tag

This repo's conventions warn against anchoring an inherit on a view's root tag, because core renamed
`<tree>` to `<list>` in 18 while keeping the old view record ids. There is no way to follow that
here: `default_order` is an attribute of the root element, so setting it means naming that element.

The tests compensate. They read the **processed** arch back through `get_view` and assert the
attribute arrived, so an anchor that stops matching fails loudly. Without that, the failure is
silent — the inherit matches nothing, no error is raised, and the Apps page carries on in its
original order.

### Sorting and language

`shortdesc` is `translate=True`, so the order follows each user's own language.

**Odoo creates every database with `LC_COLLATE 'C'`** — `modules/db.py:356` passes it whenever the
template is `template0`, which is the normal path — and `C` means byte order. A plain
`ORDER BY shortdesc` is therefore not alphabetical in the way a person means it: `CRM` sorts before
`Calendar`, because `R` (82) precedes `a` (97), and accented initials sort after `Z`. The app grid,
sorted by [`vmk_apps_menu_sort`](../vmk_apps_menu_sort) in Python with case and accents folded,
disagreed with this page until 19.0.1.2.0.

**So the module also decides how `shortdesc` is compared.** `default_order` takes field names and
cannot wrap one in a function, but the ORM builds each ORDER BY term in
`BaseModel._order_field_to_sql` (`odoo/orm/models.py:4778`), and `models/ir_module_module.py`
overrides it on `ir.module.module` for `shortdesc` alone:

- **With ICU**, it orders by `shortdesc COLLATE "und-x-icu"`, ICU's root collation: case does not
  decide the order, and accented letters sit beside their base letter, so `Éxito` follows `Exit`
  rather than `Zebra`. ICU ships with the standard PostgreSQL packages and Docker images.
- **Without ICU**, naming the collation would be an error, so it falls back to `lower(shortdesc)`,
  which fixes case but not accents. Which applies is checked once per registry, from `pg_collation`.

It reaches nothing else. Core never orders modules by `shortdesc` — its `_order` uses the technical
`name` — so the override changes only the two Apps views that ask for it, keeping the reasoning of
the section above. It is the same term core would build, with the collation added: the field
expression is still added to the query's `_order_groupby`, and direction and `NULLS` pass through.

**Odoo 20 changed the method's signature**, from `(alias, field_name, direction, nulls, query)` to
`(table, field_expr, direction, nulls)`. The alias and the query are now one `TableSQL`: the column
is `table[field_expr]`, and the query, for `_order_groupby`, is `table._query`. An override still
written for 19 raises a `TypeError` on every ordering of the model, which here means the Apps page
does not open. `addons/mass_mailing/models/mailing.py:250` is the pattern followed. The per-registry
check for ICU moved from `tools.ormcache`, deprecated in 20, to `api.ormcache`.

A stored, normalised sort key was the alternative: a column, a compute, and a recompute on every
Apps-list update, and a key per language, since `shortdesc` is translated. Ordering in the query
needs none of that.

### Known limitations

- **Sorting is by display name, not by relevance.** Odoo's `sequence` curation is gone; see above.
- **Only the two Apps views are affected.** Any other list of `ir.module.module` keeps the model's
  `_order`, including Settings → Technical → Modules if you reach it through a different action.
- **Accents need ICU.** On a PostgreSQL built without it, case is folded but accented initials still
  sort after `Z`; see above.

### Translations

The module's own name and summary are `ir.module.module` records, whose xmlid belongs to `base`
(`base.module_vmk_apps_page_sort`). On Odoo 19 that made `odoo i18n export` skip them, so they were
kept in the catalogues by hand. **On Odoo 20 the exporter writes them itself**
(`odoo/tools/translate.py:1978`, `TranslationModuleReader._export_translatable_records`, selects the
`base.module_<name>` row of each exported module), and adds the module's description, which is the
whole `README.md`, since a manifest without a `description` defaults to it
(`odoo/modules/module.py:207`). The description is left out of the catalogues: the Apps page shows
`static/description/index.html`, not that field, and nothing else displays it. The rest of the
catalogue is the three core-owned terms the export finds on the extended model, _Display Name_,
_ID_, and _Module_, which carry core's own translations.

Odoo 20 also reads the name and summary straight from a module's `.po` by their `#:` reference
(`Manifest.get_translations`, `odoo/modules/module.py:236`), so a module that is not installed yet
shows them translated in a translated database. That makes the reference lines load-bearing, and the
POT still has to carry each entry, because `PoFileReader` merges every PO against it and drops what
the merge marks obsolete once the module is installed.
`tests/test_apps_page_sort.py::TestModuleNameTranslation` fails loudly if either goes missing.
Re-run the export after any change to `README.md`, or the description entry goes stale.

### Requirements

Odoo 20. Depends on `base` only. The Python is the one `_order_field_to_sql` override above.

### Testing

```bash
odoo -d <db> -u vmk_apps_page_sort --test-enable --test-tags /vmk_apps_page_sort --stop-after-init
```
