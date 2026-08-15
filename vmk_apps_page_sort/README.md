# Apps Page Sort (`vmk_apps_page_sort`)

The Apps page at `/odoo/apps` looks unsorted because it is ordered by a field it does not display.

`ir.module.module` declares `_order = 'application desc, sequence, name'`, where `name` is the
**technical** name — `hr`, `account`, `mail`. The card shows `shortdesc`, the module's display name,
which is also the model's `_rec_name`. So Employees files under `h`, Invoicing under `a`, and
Discuss under `m`, and the result reads as no order at all.

This module orders both Apps views by the name actually on the card.

## What it changes

Two view inherits, no Python:

| View                      | Used by                        |
| ------------------------- | ------------------------------ |
| `base.module_view_kanban` | the Apps page's default kanban |
| `base.module_tree`        | its list mode                  |

Both gain `default_order="application desc, shortdesc"`. Neither carries a `default_order` in stock,
so nothing is being overridden — the views simply fall back to the model's `_order` today.

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

The comparison itself is PostgreSQL's, and **Odoo creates every database with `LC_COLLATE 'C'`** —
`service/db.py` passes it whenever the template is `template0`, which is the normal path. `C` means
byte order, so this page is not alphabetical in the way a person means it:

- `CRM` sorts before `Calendar`, because `R` (82) precedes `a` (97). Odoo has enough all-caps names
  — CRM, MRP, IoT, SMS — for them to clump at the top.
- Accented initials sort after `Z`, so a Spanish or Catalan name beginning `Á` lands at the end.

This is the one place these two modules genuinely differ:
[`vmk_apps_menu_sort`](../vmk_apps_menu_sort) folds case and accents into a Python sort key and is
alphabetical in the human sense, while this module hands the comparison to the database and inherits
its answer.

Fixing it would mean a stored, normalised sort key on `ir.module.module` and ordering on that, since
`default_order` takes field names and cannot wrap one in `lower()`. That is a column, a compute, and
a recompute on every Apps-list update, to correct the position of a handful of acronyms. Not
obviously worth it, but the option is real if the clumping grates.

## Known limitations

- **Sorting is by display name, not by relevance.** Odoo's `sequence` curation is gone; see above.
- **Only the two Apps views are affected.** Any other list of `ir.module.module` keeps the model's
  `_order`, including Settings → Technical → Modules if you reach it through a different action.
- **Byte order, not human alphabetical order**, because Odoo builds databases with `LC_COLLATE 'C'`.
  Acronyms clump at the top and accented initials fall to the end; see above.

## Translations

The module's own name and summary in `i18n/vmk_apps_page_sort.pot`, `es.po` and `ca.po` are
hand-maintained, not exported — `ir.module.module` records belong to `base`'s xmlid namespace, so
`odoo i18n export` never sees them. The module's own view attributes generate no other translatable
terms, so that is the whole of this catalogue. See
[`vmk_language_systray`'s README](../vmk_language_systray#the-modules-own-name-and-summary-are-hand-maintained-in-i18n)
for the full explanation. `tests/test_apps_page_sort.py::TestModuleNameTranslation` fails loudly if
re-running the export drops them.

## Requirements

Odoo 19. Depends on `base` only, and ships no Python beyond an empty package marker.

## Testing

```bash
odoo -d <db> -u vmk_apps_page_sort --test-enable --test-tags /vmk_apps_page_sort --stop-after-init
```
