# Protect Language Edits (`vmk_language_protect_settings`)

Stop Odoo updates from reverting your edits to language settings. In standard Odoo, every module
update resets the languages to Odoo's own values, so a renamed language or a changed date format is
quietly reverted. This module keeps your changes: a language you edit is protected from updates from
then on.

**How to use it** is in the user documentation, [`doc/index.rst`](doc/index.rst), which the Odoo
Apps Store also shows on the module's page, together with the changelog.

It depends only on `base`. LGPL-3, © 2026 Valencia Makers, SL.

## For developers

Odoo ships its languages as module data and re-applies them on every module update, so any edit you
make to a language is reverted. Rename `English (US)` to `English`, broaden Catalan's ISO code from
`ca_ES` to `ca`, and the next `-u base` — which is what `-u all` and most update scripts do — puts
both back.

This module keeps those edits. It freezes the language **record**, not its translations: the two are
unrelated, and translation updates are unaffected. Hence _protect_settings_.

### What gets reverted, and why

The values come from `base/data/res.lang.csv`, a plain CSV in base's `data` list. CSV data files
have no `noupdate` mechanism — unlike XML, which can wrap records in `<data noupdate="1">` — so
every row loads with `noupdate = False` and is re-applied on each update. The columns it resets:

`name`, `code`, `iso_code`, `direction`, `grouping`, `decimal_point`, `thousands_sep`,
`date_format`, `time_format`, `week_start`

`base/data/res_lang_data.xml` additionally sets `url_code` and `flag_image` for a handful of
languages, some of it outside its `noupdate` block. Odoo 20 loads those flags as `type="bytes"`
where 19 said `base64`; `flag_image` is still an ordinary stored `fields.Image`, so edits to it are
caught like any other.

### How it protects them

By setting `noupdate` on the language's external id. `_load_records` in `odoo/orm/models.py` decides
what to re-apply with (`odoo/orm/models.py:4676`):

```python
if not (update and d_noupdate):
    to_update.append(data)
```

so a flagged record is skipped while updating a module, but still created on a fresh install. The
flag is durable: the xmlid upsert in `ir.model.data._build_update_xmlids_query`
(`odoo/addons/base/models/ir_model.py:2490`) only ever writes `(model, res_id, write_date)`, never
`noupdate`, so the data file that created the row cannot clear it later.

Protection is per record and all-or-nothing — there is no per-field granularity. A protected
language also stops receiving genuine Odoo corrections to its date formats or week start. That is
the trade, and it is why disabled languages are left alone.

### When it applies

- **On install**, every **enabled** language is protected. Edits made before this module existed are
  already in the database and cannot be told apart from shipped values after the fact, so protecting
  the languages actually in use covers them without guessing. The ~80 disabled ones are left to
  track Odoo.
- **On edit**, a language is protected as soon as you change one of the fields listed in
  `PROTECTED_FIELDS`. Enabling or disabling a language does **not** protect it, and neither does
  reordering it with [`vmk_language_sequence`](../vmk_language_sequence) — neither is a
  customisation worth freezing a record for.
- **Never for the data loader.** `_load_records_write` (`odoo/orm/models.py:4596`) marks the
  loader's writes so Odoo re-applying its own data is not mistaken for a user edit; without that,
  the first update after install would freeze every language it touched.

A **Protect From Updates** toggle on the language form shows the state and lets you clear it,
handing that language back to Odoo.

Languages you create by hand have no external id, so no data file can overwrite them and there is
nothing to protect. The toggle stays off for them, correctly.

### A note on `iso_code`

Its help text — _"This ISO code is the name of po files to use for translations"_ — is stale.
`_load_module_terms` (`odoo/addons/base/models/ir_module.py:988`) passes the language **`code`** to
`get_po_paths` (`odoo/tools/translate.py:2421`), and `get_base_langs('ca_ES')` (`:2407`) returns
`['ca', 'ca_ES']`, so `ca.po` is found whatever `iso_code` says. What `iso_code` still drives is
`num2words`, for amounts in words (`odoo/addons/base/models/res_currency.py:256`). Changing it is
safe either way; this module just stops the change being reverted.

### `res.lang` is a `CachedModel` in Odoo 20

It caches `_cached_data_fields` — `name`, `code`, `iso_code`, `url_code`, the formats, the
separators, and `flag_image_url` — in the `'stable'` cache (`odoo/orm/models_cached.py`), and
`write()` clears that cache itself for those fields. Nothing here needs to: we write only `noupdate`
on `ir.model.data`, and `protect_from_updates` is neither cached nor stored. Our `write()` override
calls `super()` first, so the cache is already right by the time it flags the record.

### Translations

The module's own name and summary in `i18n/vmk_language_protect_settings.pot`, `es.po` and `ca.po`
were hand-maintained until Odoo 19, since `ir.module.module` records belong to `base`'s xmlid
namespace and the exporter never saw them. Odoo 20's exporter does emit them, under this module's
name, and also dumps the whole README as the module's `description`; the catalogues keep the two
short entries and leave that one out. See
[`vmk_language_systray`'s README](../vmk_language_systray#the-modules-own-name-and-summary-are-hand-maintained-in-i18n)
for the full explanation. `tests/test_language_freeze.py::TestModuleNameTranslation` fails loudly if
re-running the export drops them.

### Requirements

Odoo 20. Depends only on `base`.

### Testing

```bash
odoo -d <db> -u vmk_language_protect_settings --test-enable \
     --test-tags /vmk_language_protect_settings --stop-after-init
```

Verified end to end against `odoo:20.0` (30 September 2026): with Catalan renamed to
`Catalan / Català / Valencià` and its ISO code broadened to `ca`, and `English (US)` renamed to
`English`, a full `-u base` left both untouched — while an unprotected control language, edited the
same way, reverted to `French / Français`.
