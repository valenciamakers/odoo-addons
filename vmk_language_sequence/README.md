# Language Sequence (`vmk_language_sequence`)

Reorder languages manually instead of alphabetically. In standard Odoo, languages are always listed
alphabetically by their English name, so a Valencia business that offers _Català, English, Français,
Deutsch,_ and _Español_ will display them in that order. This module lets you drag enabled languages
into any order you choose.

**How to use it** is in the user documentation, [`doc/index.rst`](doc/index.rst), which the Odoo
Apps Store also shows on the module's page, together with the changelog.

It depends only on `http_routing`, and orders the website's selector wherever `website` is
installed. LGPL-3, © 2026 Valencia Makers, SL.

## For developers

Odoo orders languages alphabetically by name, everywhere, with no way to change it. This module adds
a `sequence` field to `res.lang` and a drag handle to **Settings → Translations → Languages**, so
the enabled languages appear in the order you choose.

The chosen order drives:

- the **website language selector** in the site header;
- the **language dropdowns** on user and contact forms;
- the Languages list itself, and any other `res.lang` search;
- which variant of a language search engines are told is the generic one, when two are enabled.

### Why it needs more than a `sequence` field

The obvious implementation — add `sequence`, override `_order` — reorders the Languages list and
nothing else. Odoo 20 made `res.lang` a `models.CachedModel`, which keeps the active languages' data
on the `'stable'` cache, and every list of languages core builds starts from that cache and sorts it
by name itself:

| Consumer                             | Path                                                         | Stock ordering                       |
| ------------------------------------ | ------------------------------------------------------------ | ------------------------------------ |
| Language dropdowns (users, contacts) | `get_installed()`                                            | `_get_active_langs().sorted('name')` |
| Portal selector (no website)         | `http_routing`'s `_get_frontend()`, `_get_active_by('code')` | `_get_active_langs()`, id order      |
| Website language selector            | `website`'s `_get_frontend()`                                | `language_ids.sorted('name')`        |

So `models/res_lang.py` does four things beyond declaring the field:

1. **`_cached_data_fields`** gains `sequence`. Two effects in one line: the cached language data
   carries it, so no ordering code needs a query of its own, and `CachedModel`'s
   `_clear_cache_on_fields` is derived from the same attribute, so writing a sequence clears the
   `'stable'` cache. It is a property that appends to `super()`'s tuple rather than a copy of it, so
   a field core adds later is not dropped.
2. **`_get_active_langs()`** returns the languages sorted by `(sequence, name)`. `_get_active_by()`
   builds its `LangDataDict` from it, so `_get_data()`, the portal selector, and every keyed view of
   the cache (`code`, `id`, `url_code`) follow the order with no override of their own — and stay
   cached by core, which matters because `_get_data()` is reached on every date and number format.
3. **`get_installed()`** is overridden, because core sorts its result by name after asking for the
   languages, which would undo point 2. It is the source of every language dropdown on users,
   contacts, mail templates, events, payments and more, and of the systray menu.
4. **`_get_frontend()`** re-sorts `website`'s result, undoing its `.sorted('name')`. No cache of its
   own — `website`'s method is already cached, and this runs once per page render over a handful of
   entries. It then re-assigns the hreflang codes, below. It is not an ordinary override; see the
   next section.

### `_get_frontend()` is patched onto the registry class

`website`'s `_get_frontend()` (`website/models/res_lang.py`) builds its list by name and returns it,
calling `super()` only when there is no current website. So an override of ours has to sit **above**
it to have any effect, and an ordinary override sits above only what its module depends on.
Depending on `website` would do that, and until 20.0.1.1.0 this module did, which installed the
Website app on every database that only wanted its language dropdowns ordered.

Instead `_register_hook()` sets the method on the `res.lang` registry class itself, the way
`base_automation` patches models (`base_automation/models/base_automation.py`, `_register_hook`).
That class is above every module's class whatever order they loaded in: here this module loads long
before `website`. The method reaches core through `super(<registry class>, self)`, resolved on each
call, since Odoo reassigns that class's bases as modules load (`odoo/orm/model_classes.py`). Every
registry load builds a fresh class and runs the hook again, so installing `website` afterwards needs
nothing, and uninstalling this module leaves nothing behind.

A patch that stops applying raises nothing, and here it would show only as the site selector going
back to name order. So the hook logs a warning if `_get_frontend` is gone from `res.lang`, the
method is marked so that a second hook call does not wrap it twice, and `TestFrontendPatch` asserts
it is in place. Written as a plain override, the two website tours and `TestHreflang` fail.

### What the order does not reach

Three places in core 20 sort `_get_active_langs()` by name themselves, in their own code, and this
module leaves them alone: the **translation dialog** (`web/controllers/webclient.py`), Studio's XML
resource editor, and the **Point of Sale self-order kiosk's** default languages
(`pos_self_order/models/pos_config.py`). The first two are for staff translating content, where
alphabetical is as good as any order. The kiosk is customer-facing, so it may be worth a patch if
you run it, but it is one more copy of core to keep in step and nobody asked for it.

Two consumers take the first language in our order as a default rather than listing them:
`get_installed()[0]` picks the language of a new survey, and `http_routing`'s `_get_default_lang`
falls back to the first active language when no default contact language is set. Both were true on
Odoo 19 too, and both are harmless while English or the company's language leads the order.

### hreflang follows the order too

`website`'s `_get_frontend()` (`website/models/res_lang.py`) also hands out each language's
`hreflang`, the code in the `<link rel="alternate">` tags that tell search engines which page is for
whom. The first variant of each base language it meets gets the short code (`en`) and the rest a
regional one (`en-us`), and it meets them in name order. Re-sorting afterwards moves the entries but
not their codes, so English (UK) stayed the generic English wherever it was dragged.

`_hreflang_in_order()` therefore runs core's loop again, over our order: the first variant in the
chosen order is generic. It keeps core's one exception, that `es_419` takes `es` whenever it is
enabled, because core treats Latin American Spanish as the generic Spanish. It is a copy of core's
rule, so re-check it against that method on a major upgrade. Without a current website — Odoo 19
keyed this on the request, 20 keys it on `env.website` — the data carries no hreflang, and passes
through untouched.

The consequence is that dragging a language now changes a search-engine signal, which is the point —
someone who puts English (UK) first means it — but worth knowing before reordering for looks.

**Core's `website` test `test_alternate_hreflang` fails with this module installed**, and should. It
enables French (FR), then French (BE) and French (CA), and asserts that French (BE) is generic,
because it is first by name. Here French (FR) was enabled first, so it is first in the order and
generic. `TestHreflang` covers the same ground in our order, including the `es_419` exception.

### Why no cache invalidation of our own

`_get_frontend()` takes its order from `_get_active_by('code')` rather than from the `sequence`
inside the data core hands back, and that is the whole reason `write()` needs no cache clearing.

`website._get_frontend` is cached on the `'default'` cache, which nothing invalidates when a
sequence changes. Sorting on the values baked into _that_ cache would mean clearing all of it on
every reorder — every compiled QWeb template and view lookup on the site — to shift four languages.
`_get_active_by` is on `'stable'`, and `CachedModel.write` clears `'stable'` when a written field is
in `_clear_cache_on_fields`, which is why `sequence` has to be in `_cached_data_fields`: Odoo 19
cleared it on every write to `res.lang`, but 20 clears it only for those fields (`orm/models.py`,
`write`). Without that, a drag would leave the dropdowns and the site selector stale.
`env.invalidate_ormcache(name)` is what 20 has in place of `Registry.clear_cache()`, and it too
takes a cache _name_, so there is no narrower option.

One consequence: the `sequence` inside `website._get_frontend`'s own data can be stale, and nothing
reads it.

`LangDataDict` and `LangData` are `Mapping`s in 20, with a real `__contains__`, so
`"es_419" in langs` now answers honestly; `.get()` still returns the dummy entry for any key, since
it is built on `__getitem__`. Odoo 19's trap, that `in` was always true, is gone.

### `_order`, and what actually orders the Languages list

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

### Why sequences are seeded on install

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

### Known limitations

- **The Languages list is developer-mode only.** Both Settings → Translations → Languages and the
  Manage Languages button in General Settings carry `groups="base.group_no_one"` in stock Odoo, so a
  non-developer admin cannot reach the drag handles. Enable developer mode, or go straight to
  `/odoo/action-base.res_lang_act_window`. This module adds no menu of its own.

### Translations

The module's own name and summary are in `i18n/vmk_language_sequence.pot`, `es.po` and `ca.po`. Odoo
20's `i18n export` writes them, under the module itself, beside a `description` entry holding the
whole of this README, which we delete from the POT and the POs: nothing displays it. See
[`vmk_language_systray`'s README](../vmk_language_systray#the-modules-own-name-and-summary-in-i18n)
for the full explanation. `tests/test_language_sequence.py::TestModuleNameTranslation` fails loudly
if a re-export drops them.

### Requirements

Odoo 20. Depends on `http_routing`, which defines `_get_frontend()` and itself needs only `web`.
`website` is optional: where it is installed, before or after this module, its language selector and
hreflang codes follow the order.

### Testing

```bash
# unit tests
odoo -d <db> -u vmk_language_sequence --test-enable --test-tags /vmk_language_sequence \
     --stop-after-init
```

**Browser tests.** `tests/test_tours.py` runs tours from `static/tests/tours/` in headless Chrome,
with sequences set so that the order is not alphabetical (French, English, Catalan, Spanish): the
`vmk_language_systray` dropdown lists the languages in that order, the website's language selector
does too (as a visitor and logged in), and dragging a row by its handle in the Languages list
(developer mode) resequences the languages. The drag needs two moves, one past the tolerance over
the dragged row and then one onto the target, because Sortable binds its `pointerenter` handlers
only when the drag starts. The systray tour needs `vmk_language_systray` installed alongside, and is
skipped without it. The two website tours and `TestHreflang` are skipped on a database without
`website`, and a skip reads as a pass, so run the tests once with `website` installed as well as
once without.
