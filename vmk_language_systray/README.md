# Language Systray (`vmk_language_systray`)

A globe icon in the backend systray, next to the company switcher. It lists the active languages;
clicking one sets the **current user's** backend interface language and reloads. It never touches
the website's frontend language, and it is invisible in a single-language database.

## Showing the language name (off by default)

The button is a bare globe. The systray is a crowded, fixed-width row, and a word as wide as
`English (US)` should cost that space only for someone who has asked for it — so the name is opt-in,
through a system parameter with no settings-page entry of its own:

| Where | Settings → Technical → System Parameters (developer mode) |
| ----- | --------------------------------------------------------- |
| Key   | `vmk_language_systray.show_name`                          |
| Value | `True`                                                    |

Deliberately not surfaced anywhere in the interface. Someone who wants it can go and set it; nobody
else has to see a toggle for it. Even switched on, the name still only appears at the `lg`
breakpoint and up, where the row has room.

An `ir.config_parameter` rather than a field of ours because it is the one hidden switch in Odoo
that already has a screen to set it on. The cost is that it is **database-wide, not per-user** — the
per-user home for this would be `res.users.settings`, but that model lives in `mail` (a dependency
this module does not otherwise need) and ships no menu or action at all, so setting it by hand would
mean `odoo shell`. A screen beat a scope here.

## Why this is almost entirely assets

One file of Python: `models/ir_http.py`, which puts the flag above into `session_info`. That is not
a convenience — `ir.config_parameter` is readable only by `base.group_system`, so a plain internal
user cannot query it and the value has to be handed to them under `sudo()`. Core solves the same
problem the same way for `web.quick_login`, a screen up in `web/models/ir_http.py`.

Everything else the module needs already exists in core with the right access already granted, so
there is nothing for a Python model to add:

- `res.lang.get_installed()` is `@api.model`, and `base.group_user` has read access on `res.lang`
  (`base/security/ir.model.access.csv`), so a plain internal user can call it directly.
- `lang` is in `res.users.SELF_WRITEABLE_FIELDS` (`base/models/res_users.py:189-193`), and
  `res.users.write()` sudo's the record when every key in `vals` is self-writeable (`:605-615`). Any
  internal user can therefore set their own `lang` with no extra rights.

That second point is narrower than it looks: the sudo path only triggers when **every** key in the
write is self-writeable. `language_systray.js` writes `{ lang: code }` alone for exactly this reason
— adding anything else to that call, even something else self-writeable in a different combination
check, risks falling back to needing ordinary write access on `res.users`, which a non-admin user
does not have. `tests/test_language_systray.py` asserts both halves of this: `lang` alone succeeds
for a plain internal user, and `lang` paired with `login` (not self-writeable) raises `AccessError`.

No `security/ir.model.access.csv` either. ACLs are per model, and `ir.http` is an abstract model
with no table; inheriting it to extend one method grants nothing and needs nothing.

## Gating on `isDisplayed`, not a `t-if`

`localization.multiLang` (`@web/core/l10n/localization`) is already `len(get_installed()) > 1`, set
once by the localization service. The systray registry entry's `isDisplayed(env)` predicate
(`web/static/src/webclient/navbar/navbar.js`'s `systrayItems` getter) is where that gate lives,
rather than a `t-if` inside the template. The difference matters: a `t-if` would still mount the
component and fire its `onWillStart` RPC in a single-language database, paying for a dropdown nobody
can meaningfully use. `isDisplayed` stops the component being created at all.

## Placement

The same `systrayItems` getter reverses the systray list before rendering, so a **lower** sequence
renders **further right**. `web.user_menu` is sequence 0 and `SwitchCompanyMenu` is 1; this
registers at sequence 2, immediately to their left.

The root element is `d-none d-md-block`, so the control is **absent below the `md` breakpoint** —
there is no way to change language from a phone-width backend. That is deliberate, matching
`web.UserMenu` and `SwitchCompanyMenu`, which both disappear at the same width and hand over to the
burger menu; adding a burger entry here would be the fix if it ever matters.

## Reusing `vmk_language_sequence`'s order, and not sorting again

`get_installed()` reads `_get_active_by('code')`, the method our own `vmk_language_sequence` module
overrides to sort by `(sequence, name)` instead of core's plain `name`. So when that module is
installed, the list this module receives from `get_installed()` **already** reflects the hand-picked
order — sorting it again client-side would silently undo that work. This module does not depend on
`vmk_language_sequence` (which pulls in `website`, which this must not); the integration is soft,
and holds whether or not that module is present.

## Trimming the name, and why `title`/`aria-label` need it that core's own text nodes do not

Language names come back as `"Spanish / Español"` or, for a language with no slash,
`"English (US)"`. Core displays them with `name.split('/').pop()` (see e.g.
`portal.language_selector`), and gets away with the resulting leading space — `" Español"` — because
it only ever lands in an HTML text node, where the browser collapses it. This module puts the same
trimmed name in a `title` and an `aria-label`, where whitespace is not collapsed, so it also calls
`.trim()`. `tests/test_language_systray.py` drives that assertion off a real `res.lang` record
rather than a literal string, so a future change to Odoo's own naming convention would surface
there.

## `localization.code`, not `user.lang`

The active entry is matched against `localization.code` — the current user's language in Odoo form
(`es_ES`), set by the localization service. `user.lang` is the _browser_ locale form (`es-ES`) and
never equals a `res.lang` code, so it cannot be used for this comparison.

## Marking the active language, twice

The active `DropdownItem` gets `class="{ selected: isActive(lang) }"`, following
`control_panel.xml`'s view switcher and `report_view_measures.xml` rather than inventing a marker of
our own. Core's global `:not(.dropstart) > .dropdown-item.selected` rule
(`web/static/src/webclient/webclient.scss`) already bolds it and draws a checkmark — no CSS of our
own is needed.

That marker is **visual only**, which is easy to miss because it looks complete on screen. The
checkmark is a FontAwesome glyph in a `:before` pseudo-element and the emphasis is a `font-weight`,
so neither reaches the accessibility tree: a screen reader running down the list is told nothing
about which language is currently in force. The items therefore also carry
`attrs="{ role: 'menuitemradio', 'aria-checked': … }"`. `attrs` is `DropdownItem`'s own escape hatch
— `web.DropdownItem` spreads it through `t-att` after its static `role="menuitem"`, so the later
value wins — and `menuitemradio` is the correct role for a single-select list, matching what core
does for `web.CheckboxItem`.

## Accessibility: the button says what it does, not just what it reads

The button is a bare globe by default, and still icon-only below the `lg` breakpoint even when
`show_name` is on. So there is usually no visible text at all, and `aria-label`/`title` are the only
accessible name it has — which is why the name is `Language: Español`, not the bare `Español`.

The distinction is the whole point. A bare language name announces as "Español, button", which says
what the control _reads_ and nothing about what it _does_; with only a globe on screen, there is
nothing else to infer purpose from. Core draws the same line for the directly equivalent control:
`switch_company_item.xml`'s aria-label is `'Switch to ' + props.company.name`, not the company name
alone. Naming the language inside the label rather than replacing it also keeps the accessible name
a superset of the visible text in the case where the name _is_ shown, which is what WCAG 2.5.3
(Label in Name) asks for.

The globe carries `fa-lg`, matching the messaging and activity icons beside it (`fa-lg fa-comments`,
`fa-lg fa-clock-o`). Without it FontAwesome inherits 14px against their 18.41px and the globe reads
as visibly undersized — a difference that only shows up in the rendered row, not in the source.

`buttonLabel` falls back to plain `Language` when `activeLanguage` is undefined. That is not
defensive padding: the localization service falls back to `browser.navigator.language` when the
user's context carries no lang, so a browser set to `en-GB` against a database without `en_GB`
leaves `localization.code` matching nothing in the list. Without the fallback the button would have
no accessible name at all in that case, since the visible span is `t-if`'d out too.

## Translations

Two authored terms, both in `language_systray.js`: `Language` and `Language: %s`. Everything else on
screen is a language's own name, which is data rather than a term to translate. The catalogues also
carry `Display Name`, `HTTP Routing` and `ID`, which are not ours — inheriting `ir.http` attributes
that model's name and its `display_name`/`id` fields to this module in the export — so they take
core's wording verbatim.

`Language` is one core already owns — `base` translates it `Idioma` in both Spanish and Catalan — so
`es.po` and `ca.po` reuse that wording rather than introducing a second vocabulary for the same
word, and `Language: %s` follows it.

Worth recording why this module nearly shipped without an `i18n/` at all: before the accessible name
was fixed, the only strings it contained were language names taken from the database, so
`i18n export` genuinely returned an empty `.pot`. That emptiness was a symptom of the accessibility
gap, not an independent finding — the module had no authored strings precisely because it was not
saying anything to a screen reader. An empty POT is worth a second look for that reason before
concluding, as `vmk_settings_sort` and `vmk_apps_page_sort` legitimately did, that no catalogue is
needed.

## Testing

```bash
cd dev
docker compose run --rm odoo odoo -d test --init vmk_language_systray --without-demo=all \
    --stop-after-init
docker compose run --rm odoo odoo -d test -u vmk_language_systray --test-enable \
    --test-tags /vmk_language_systray --stop-after-init
```

## License

MIT. See `LICENSE`. Declared in the manifest as `"Other OSI approved licence"`, which is the only
value Odoo's `Selection` accepts for it.
