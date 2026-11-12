# Custom Colors (`vmk_colorlist_colors`)

Change the twelve colors Odoo offers wherever a record has a color — tags, kanban cards, calendars,
and the color picker itself — and rename them. The slots and what each one means stay Odoo's: this
changes how each color looks and what it is called, not how many there are.

It depends only on `base_setup`, so it works on Community and Enterprise alike. LGPL-3, © 2026
Valencia Makers, SL.

## How to use it

In **Settings › General Settings › Colors**, **Edit Colors** opens the twelve colors in a list.

- **Pick a color** with the color picker on its row. Picking Odoo's own color again removes the
  custom one.
- **Rename a color** by typing a name over Odoo's, which shows in the field until you do. A name is
  translatable, like any other. Left empty, the color keeps Odoo's name, in Odoo's translations. “No
  color” keeps its name, since Odoo gives it a meaning of its own: an event tag without a color is
  hidden from the website, for one.
- **The × at the end of a row** puts that color's Odoo color and name back, and **Reset to
  Defaults** does it for all twelve, after asking. Both reload the page, so the change shows
  everywhere at once. A color picked in the list shows elsewhere after the next reload.

Only users with the Settings access right (Administration › Settings) reach the list.

## For developers

### Where Odoo's colors come from

A record's color is an integer, 0 to 11, and Odoo draws it from two places that this module has to
reach:

- **The stylesheets.** `$o-colors` in `web/static/src/scss/primary_variables.scss` holds the twelve
  colors, and three lists beside it hold the shades Odoo picked by hand for tags and badges: a
  border, a light background, and a dark text color (`$o-colors-border`, `$o-colors-bg-subtle`, and
  `$o-colors-text-emphasis`). Every class drawn from a color index is compiled from these: the color
  picker's swatches (`o_colorlist_item_color_N`), tags (`o_tag_color_N`), badges, kanban color
  bands, calendar colors, and the website's `o_color_N`. Enterprise's dark mode sets its own, in
  `web_enterprise/static/src/scss/primary_variables.dark.scss`.
- **The names**, in `ColorList.COLORS` (`web/static/src/core/colorlist/colorlist.js`), a static
  array of translated strings that every picker shows as the swatches' titles.

### The stylesheets

Odoo compiles SCSS when it builds a bundle, from files and from attachments: an `ir.asset` record
can name an attachment's URL as a path, which is how website saves the stylesheets its editor
customizes (`website.assets.save_asset`). That part is `base`'s, so this module does the same
without depending on website.

Whenever a custom color changes, `_update_stylesheets()` writes two SCSS files as attachments, at
`/_custom/vmk_colorlist_colors/colors.scss` and `colors.dark.scss`, and two `ir.asset` records
putting them in the bundles:

- **The light one goes first in `web._assets_primary_variables`** (`prepend`). Odoo's values are all
  `!default`, so ours, set before them, stand: in the backend, in the website's frontend bundles,
  which include the same variables, and everywhere else that compiles them. Nothing of core's is
  replaced or patched.
- **The dark one goes just before it in `web.dark_mode_variables`**, a bundle only Enterprise has.
  Enterprise's dark variables are not set the same way: `$o-colors` there is built by appending each
  color of `$o-colors-original`, darkened, to an empty list. Our light stylesheet, being first,
  would have set `$o-colors` already, and Enterprise would append its twelve to our twelve. So the
  dark stylesheet sets `$o-colors-original` and the dark shades, and sets `$o-colors` to an empty
  list; the light stylesheet's values are `!default` too, so in the dark bundle they leave it empty
  for Enterprise to fill. `tests/test_colors.py` compiles both bundles and checks there are still
  twelve colors.

Both files hold all twelve colors: Odoo's for the slots nobody changed, from `models/palette.py`,
which keeps a copy of Odoo's values. `tests/test_palette.py` reads Odoo's SCSS and fails if Odoo
changes them, rather than letting an update mix our copy with its new values. When no color is
custom, both attachments and both asset records are deleted, and Odoo compiles exactly as it would
without the module. An `uninstall_hook` deletes them too: they are records the module made at run
time, not its data, so uninstalling would otherwise leave the custom colors in place with nothing to
change them back.

Writing an attachment that a bundle already names does not change the bundle's list of files, which
is what Odoo caches the bundle by, so the module clears the `assets` cache, as website does when it
saves a customized stylesheet.

### The shades, in OKLCH

Odoo's comment on its three shade lists says they were made in OKLCH, and read in OKLCH they follow
a rule: each shade keeps its color's hue, all the shades of one role share nearly one lightness (in
light mode, 0.65 for borders, about 0.90 for backgrounds, and 0.36 for text; in dark, 0.76, about
0.32, and 0.88), and each role caps the chroma. Odoo compiles SCSS with libsass, which has no OKLCH,
so `palette.shades()` computes a custom color's shades in Python by that rule and writes the hex
values. A shade outside sRGB loses chroma until it fits, keeping its lightness and hue, as CSS's own
gamut mapping does. Put through the same function, Odoo's own colors come out within a few
hundredths of Odoo's lightness for every shade, which `tests/test_palette.py` checks.

### The names

A custom name is stored on the record, translatable, and empty until someone types one, so an
untouched color keeps Odoo's name and Odoo's translations of it. The custom names reach the web
client in the session, in the user's language (`ir.http.session_info`, `models/ir_http.py`), and
`static/src/colorlist.js` writes them into `ColorList.COLORS` when the backend loads. It changes the
array in place rather than replacing it: the kanban record takes `const { COLORS } = ColorList` when
its module loads, and would keep the old array.

The list shows Odoo's name as the name field's placeholder, through web's `placeholder_field`
option. Odoo's names are JavaScript terms of `web`, so their translations are web's JavaScript
catalogue, which Python's `_()` does not read: `_odoo_names()` takes them from
`code_translations.get_web_translations`, the same source the web client loads.

### Translations

The module's own name and summary are `ir.module.module` records whose xmlid belongs to `base`
(`base.module_vmk_colorlist_colors`). Odoo 20's `i18n export` writes them into the catalogue, beside
a `description` entry holding this whole README, which we leave out: nothing displays it.
`tests/test_translations.py` fails if the POT loses either entry, which would otherwise leave the
name in English in a translated database without a word. Terms core already translates are taken in
core's wording. Odoo's _Slot_ is _Espacio_ and _Ranura_, for an event's time slot; a color's slot is
its position in the list, so _Posición_ and _Posició_.

### Testing

`tests/test_palette.py` holds the copy of Odoo's values to Odoo's own files and checks the OKLCH
conversion. `tests/test_colors.py` checks the records, their access, both stylesheets and their
asset records as colors change and reset, the compiled bundles, and the names in the session in two
languages. `tests/test_tours.py` drives the list from General Settings, the reset button, and a
contact tag's color picker, whose swatch must carry the new name and be drawn in the new color.
