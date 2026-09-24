# Apps Page Sort (`vmk_apps_page_sort`)

The Apps page at `/odoo/apps` looks unsorted because it is ordered by a field it does not display.

`ir.module.module` declares `_order = 'application desc, sequence, name'`, where `name` is the
**technical** name — `hr`, `account`, `mail`. The card shows `shortdesc`, the module's display name,
which is also the model's `_rec_name`. So Employees files under `h`, Invoicing under `a`, and
Discuss under `m`, and the result reads as no order at all.

This module orders both Apps views by the name actually on the card.

## What it changes

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

## Why the views rather than `_order`

Overriding `_order` on `ir.module.module` is one line and reaches every module list at once, which
is precisely the problem: that model is searched during install and upgrade paths, not only for
display. A `default_order` on the two views confines the change to the screens this module is about.

This is the same reasoning as [`vmk_apps_menu_sort`](../vmk_apps_menu_sort) sorting the menu payload
instead of writing `sequence` values — order the presentation, leave the data alone.

## Why both records anchor on the root tag

This repo's conventions warn against anchoring an inherit on a view's root tag, because core renamed
`<tree>` to `<list>` in 18 while keeping the old view record ids. There is no way to follow that
here: `default_order` is an attribute of the root element, so setting it means naming that element.

The tests compensate. They read the **processed** arch back through `get_view` and assert the
attribute arrived, so an anchor that stops matching fails loudly. Without that, the failure is
silent — the inherit matches nothing, no error is raised, and the Apps page carries on in its
original order.

## Sorting and language

`shortdesc` is `translate=True`, so the order follows each user's own language.

**Odoo creates every database with `LC_COLLATE 'C'`** — `service/db.py` passes it whenever the
template is `template0`, which is the normal path — and `C` means byte order. A plain
`ORDER BY shortdesc` is therefore not alphabetical in the way a person means it: `CRM` sorts before
`Calendar`, because `R` (82) precedes `a` (97), and accented initials sort after `Z`. The app grid,
sorted by [`vmk_apps_menu_sort`](../vmk_apps_menu_sort) in Python with case and accents folded,
disagreed with this page until 19.0.1.2.0.

**So the module also decides how `shortdesc` is compared.** `default_order` takes field names and
cannot wrap one in a function, but the ORM builds each ORDER BY term in
`BaseModel._order_field_to_sql` (`odoo/orm/models.py`), and `models/ir_module_module.py` overrides
it on `ir.module.module` for `shortdesc` alone:

- **With ICU**, it orders by `shortdesc COLLATE "und-x-icu"`, ICU's root collation: case does not
  decide the order, and accented letters sit beside their base letter, so `Éxito` follows `Exit`
  rather than `Zebra`. ICU ships with the standard PostgreSQL packages and Docker images.
- **Without ICU**, naming the collation would be an error, so it falls back to `lower(shortdesc)`,
  which fixes case but not accents. Which applies is checked once per registry, from `pg_collation`.

It reaches nothing else. Core never orders modules by `shortdesc` — its `_order` uses the technical
`name` — so the override changes only the two Apps views that ask for it, keeping the reasoning of
the section above. It is the same term core would build, with the collation added: the field
expression is still added to the query's `_order_groupby`, and direction and `NULLS` pass through.

A stored, normalised sort key was the alternative: a column, a compute, and a recompute on every
Apps-list update, and a key per language, since `shortdesc` is translated. Ordering in the query
needs none of that.

## Known limitations

- **Sorting is by display name, not by relevance.** Odoo's `sequence` curation is gone; see above.
- **Only the two Apps views are affected.** Any other list of `ir.module.module` keeps the model's
  `_order`, including Settings → Technical → Modules if you reach it through a different action.
- **Accents need ICU.** On a PostgreSQL built without it, case is folded but accented initials still
  sort after `Z`; see above.

## Translations

The module's own name and summary in `i18n/vmk_apps_page_sort.pot`, `es.po` and `ca.po` are
hand-maintained, not exported — `ir.module.module` records belong to `base`'s xmlid namespace, so
`odoo i18n export` never sees them. The module's own view attributes generate no other translatable
terms, so that is the whole of this catalogue. See
[`vmk_language_systray`'s README](../vmk_language_systray#the-modules-own-name-and-summary-are-hand-maintained-in-i18n)
for the full explanation. `tests/test_apps_page_sort.py::TestModuleNameTranslation` fails loudly if
re-running the export drops them.

## Requirements

Odoo 19. Depends on `base` only. The Python is the one `_order_field_to_sql` override above.

## Testing

```bash
odoo -d <db> -u vmk_apps_page_sort --test-enable --test-tags /vmk_apps_page_sort --stop-after-init
```
