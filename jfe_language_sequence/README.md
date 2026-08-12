# Language Sequence (`jfe_language_sequence`)

Odoo orders languages alphabetically by name, everywhere, with no way to change it. This module adds
a `sequence` field to `res.lang` and a drag handle to **Settings → Translations → Languages**, so the
enabled languages appear in the order you choose.

The chosen order drives:

- the **website language selector** in the site header;
- the **language dropdowns** on users and contacts;
- the Languages list itself, and any other `res.lang` search.

## Why it needs more than a `sequence` field

The obvious implementation — add `sequence`, override `_order` — reorders the Languages list and
nothing else. Three separate code paths produce language lists, and none of them consults `_order`:

| Consumer                       | Path                                       | Stock ordering                          |
| ------------------------------ | ------------------------------------------ | --------------------------------------- |
| Language dropdowns (users, contacts) | `get_installed()` → `_get_active_by()` | `search_fetch(..., order='name')`       |
| Portal selector (no website)   | `http_routing`'s `_get_frontend()`         | same, via `_get_active_by()`            |
| Website language selector      | `website`'s `_get_frontend()`              | `language_ids.sorted('name')`           |

So `models/res_lang.py` does four things beyond declaring the field:

1. **`CACHED_FIELDS`** gains `sequence`, so the cached language data carries it and the two sorting
   overrides below never need a query of their own.
2. **`_get_active_by()`** re-sorts by `(sequence, name)`. It is the single chokepoint behind both the
   backend dropdowns and the portal selector, so one override covers both. It keeps its own
   `ormcache` because `_get_data()` reaches it on every date and number format.
3. **`_get_frontend()`** re-sorts, undoing `website`'s `.sorted('name')`. No cache of its own —
   `super()` is already cached, and this runs once per page render over a handful of entries.
4. **`write()`** calls `registry.clear_cache()` when `sequence` changes. Odoo's own
   `res.lang.write()` clears only the `'stable'` cache, while `website._get_frontend` is cached on
   the default one; without this the site selector keeps serving the previous order.
   `website/models/website.py` does the same thing for the same reason.

## `_order` keeps `active desc` first

`_order` is `active desc, sequence, name`, not `sequence, ...`. The Languages action opens with
`active_test: False`, so the list shows all ~80 languages Odoo ships, not just the enabled ones.
Keeping the enabled ones grouped on top preserves the stock list, and means a newly activated
language surfaces into that group instead of staying buried among the disabled ones. Everything that
consumes the order sees only active languages, so the prefix is inert for them.

No install hook seeds the sequence values. Every language starts at the default `10`, so ordering is
identical to stock Odoo until you drag something — and because Odoo's resequencing rewrites the whole
list as soon as it finds tied values, the first drag assigns distinct sequences to every language in
its current order.

## Known limitations

- **Disabled languages cannot be ranked above enabled ones.** Dragging one there appears to work, then
  snaps back on reload, because `active desc` sorts first. Reordering disabled languages is
  meaningless for this feature anyway.
- **hreflang short codes still follow name order.** When two variants of one base language are active
  (`es_ES` and `es_419`, say), Odoo gives the generic `hreflang="es"` to whichever it meets first and
  region-qualifies the rest. That decision happens inside `website`'s `_get_frontend()` before this
  module re-sorts, so the manual order does not influence it. Only relevant with two variants of the
  same base language; unrelated base languages each get their own short code regardless.

## Requirements

Odoo 19. Depends on `website`, which supplies the `_get_frontend()` override point that makes the site
selector follow the order. On a database without `website`, split this into a `base`-only module plus
an `auto_install` bridge carrying override 3.

## Testing

```bash
# unit tests
odoo -d <db> -u jfe_language_sequence --test-enable --test-tags /jfe_language_sequence \
     --stop-after-init
```

Verified against `odoo:19` with English, Spanish, French and Catalan enabled: reordering in the
backend reordered the site selector live, without a server restart.
