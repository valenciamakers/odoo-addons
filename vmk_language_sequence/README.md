# Language Sequence (`vmk_language_sequence`)

Odoo orders languages alphabetically by name, everywhere, with no way to change it. This module adds
a `sequence` field to `res.lang` and a drag handle to **Settings → Translations → Languages**, so
the enabled languages appear in the order you choose.

The chosen order drives:

- the **website language selector** in the site header;
- the **language dropdowns** on users and contacts;
- the Languages list itself, and any other `res.lang` search.

## Why it needs more than a `sequence` field

The obvious implementation — add `sequence`, override `_order` — reorders the Languages list and
nothing else. Three separate code paths produce language lists, and none of them consults `_order`:

| Consumer                             | Path                                   | Stock ordering                    |
| ------------------------------------ | -------------------------------------- | --------------------------------- |
| Language dropdowns (users, contacts) | `get_installed()` → `_get_active_by()` | `search_fetch(..., order='name')` |
| Portal selector (no website)         | `http_routing`'s `_get_frontend()`     | same, via `_get_active_by()`      |
| Website language selector            | `website`'s `_get_frontend()`          | `language_ids.sorted('name')`     |

So `models/res_lang.py` does three things beyond declaring the field:

1. **`CACHED_FIELDS`** gains `sequence`, so the cached language data carries it and the two sorting
   overrides below never need a query of their own.
2. **`_get_active_by()`** re-sorts by `(sequence, name)`. It is the single chokepoint behind both
   the backend dropdowns and the portal selector, so one override covers both. It keeps its own
   `ormcache` because `_get_data()` reaches it on every date and number format.
3. **`_get_frontend()`** re-sorts, undoing `website`'s `.sorted('name')`. No cache of its own —
   `super()` is already cached, and this runs once per page render over a handful of entries.

### Why no cache invalidation of our own

`_get_frontend()` reads its sequence values from `_get_active_by()` rather than from the data
`super()` hands back, and that is the whole reason `write()` needs no `registry.clear_cache()`.

`website._get_frontend` is cached on the `'default'` cache, which nothing invalidates when a
sequence changes. Sorting on the values baked into _that_ cache would mean clearing all of it on
every reorder — every compiled QWeb template and view lookup on the site — to shift four languages.
`_get_active_by` is on `'stable'`, which core's own `res.lang.write()` already clears, so reading
the sequences from there makes a drag invalidate only the language data. Odoo 19 offers no narrower
option: `Registry.clear_cache()` takes cache _names_, and the old per-method
`ormcache.clear_cache()` is gone.

One trap worth knowing if you touch this. `_live_sequences()` deliberately builds a plain `dict`,
because `LangDataDict.__getitem__` returns a dummy entry for unknown keys rather than raising — and
`Mapping.__contains__` is implemented on top of `__getitem__`, so `code in some_lang_data_dict` is
**always true** and cannot detect a missing language.

## `_order`, and what actually orders the Languages list

`_order` is `active desc, sequence, name`. The `active desc` prefix is kept so that a plain
`res.lang.search()` anywhere in Odoo keeps returning enabled languages first, as it does in stock
(`active desc, name`); `sequence` merely replaces `name` as the tiebreak.

It does **not** order the Languages list, though. When a list view carries a handle field and sets
no `default_order`, the web client substitutes its own — `list_arch_parser.js` does:

```js
if (!treeAttr.defaultOrder.length && handleField) {
  const handleFieldSort = `${handleField}, id`;
  treeAttr.defaultOrder = stringToOrderBy(handleFieldSort);
}
```

So the Languages list is fetched `sequence, id`, ignoring `_order` entirely — and that is not
avoidable by naming an order of our own. Setting `default_order` does override the client's choice,
but `canResequenceRows` only allows dragging when `orderBy[0].name` _is_ the handle field:

```js
return !orderBy.length || (orderBy.length && orderBy[0].name === handleField);
```

Any order that groups enabled languages first has to start with `active desc`, which would silently
disable drag and drop. The grouping therefore has to live in the sequence **values** rather than in
the sort order.

## Why sequences are seeded on install

`post_init_hook` (`hooks.py`) gives enabled languages a low block — 10, 20, 30… by name — and parks
the ~80 disabled ones above `DISABLED_SEQUENCE_BASE` (10000). Without it every language shares the
default `10`, `id` becomes the only tiebreak, and the enabled languages scatter through the disabled
ones — a regression against stock Odoo, where this list is ordered `active desc, name`. Seeding
reproduces the stock grouping.

Distinct values matter for a second reason. Odoo rewrites only the records _between_ the two
positions of a drag when the sequences it sees are strictly increasing; on tied values it
resequences the entire list instead (`reorderAll` in `utils.js`). Seeded, a drag among the enabled
languages leaves the disabled block untouched.

`create()` and `write()` keep this true over time. Enabling a language moves it to the end of the
enabled block rather than leaving it stranded at its seeded value among the disabled ones, and
disabling one moves it the other way.

A language added by hand — one Odoo does not ship, created through the New button on the Languages
list — is parked the same way, into whichever block matches the `active` value it was created with.
Without that it would keep the field default of `10` and wedge itself among the enabled languages
even though `res.lang` declares `active = fields.Boolean()` with no default, so a new language is
disabled. It would also tie with whatever already sits on `10`, costing the strictly increasing
sequences that keep a drag local. An explicit `sequence` in the create values is left alone.

The field's own default is `DISABLED_SEQUENCE_BASE` rather than Odoo's customary `10`, for the same
reason: a language created without an explicit `active` is disabled, so that is the block it belongs
in. `create()` re-parks it immediately, so the default is visible only if that ever fails — and
failing to the head of the disabled languages is much better than wedging in among the enabled ones.

## Known limitations

- **The Languages list is developer-mode only.** Both Settings → Translations → Languages and the
  Manage Languages button in General Settings carry `groups="base.group_no_one"` in stock Odoo, so a
  non-developer admin cannot reach the drag handles. Enable developer mode, or go straight to
  `/odoo/action-base.res_lang_act_window`. This module adds no menu of its own.
- **hreflang short codes still follow name order.** When two variants of one base language are
  active (`es_ES` and `es_419`, say), Odoo gives the generic `hreflang="es"` to whichever it meets
  first and region-qualifies the rest. That decision happens inside `website`'s `_get_frontend()`
  before this module re-sorts, so the manual order does not influence it. Only relevant with two
  variants of the same base language; unrelated base languages each get their own short code
  regardless.

## Requirements

Odoo 19. Depends on `website`, which supplies the `_get_frontend()` override point that makes the
site selector follow the order. On a database without `website`, split this into a `base`-only
module plus an `auto_install` bridge carrying override 3.

## Testing

```bash
# unit tests
odoo -d <db> -u vmk_language_sequence --test-enable --test-tags /vmk_language_sequence \
     --stop-after-init
```

Verified against `odoo:19` with English, Spanish, French and Catalan enabled: reordering in the
backend reordered the site selector live, without a server restart.
