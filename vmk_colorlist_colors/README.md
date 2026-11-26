# Custom Colors (`vmk_colorlist_colors`)

Change the eleven colors Odoo offers wherever a record has a color — tags, kanban cards, calendars,
and the color picker itself — and rename them. The slots and what each one means stay Odoo's: this
changes how each color looks and what it is called, not how many there are. Odoo's twelfth choice,
“No color”, stays as it is.

It depends only on `base_setup`, so it works on Community and Enterprise alike. LGPL-3, © 2026
Valencia Makers, SL.

**How to use it** is in the user documentation, [`doc/index.rst`](doc/index.rst), which the Odoo
Apps Store also shows on the module's page, together with the changelog. The list's undo arrow
follows core's Replenishment list, which puts back a quantity typed over the computed one the same
way.

### Colors some apps give a meaning

The manual carries this as a list; the table here is the record of what was checked.

Most colors are only what someone picked for a tag, a stage, or a calendar, and any of them can be
replaced. A few of Odoo's apps, though, set a record's color themselves, as a traffic light. A color
replaced with one of another kind loses that meaning there: keep Red a red, Orange an orange, and
Green a green, tuned to your palette, if you run any of these apps.

| Color        | Means              | Where Odoo sets it                                                                                                        |
| ------------ | ------------------ | ------------------------------------------------------------------------------------------------------------------------- |
| Red          | Something is wrong | Attendances: a shift over 16 hours, or a missed check-out. Helpdesk: an SLA failed. Helpdesk timesheets: hours overspent. |
| Orange       | A warning          | Helpdesk timesheets: hours used up. Gamification: a goal failed. ESG: data out of date.                                   |
| Green        | All is well        | Attendances: checked in now. Helpdesk: an SLA reached.                                                                    |
| Purple, Teal | Done, up to date   | Gamification: a goal reached (Purple). ESG: data up to date (Teal).                                                       |

A few screens also draw a label in a fixed color: in Point of Sale for restaurants, a table in Red
and the selected course in Green. Checked against Odoo 19 Community and Enterprise on 26
November 2026. Odoo 20's manual also names some ShipStation labels and a recipient in Mail, for
which 19's source has no counterpart.

## For developers

### Where Odoo's colors come from

A record's color is an integer, 0 to 11, and Odoo draws it from two places that this module has to
reach:

- **The stylesheets.** `$o-colors` in `web/static/src/scss/secondary_variables.scss` holds the
  twelve colors, and **Odoo 19 derives everything else from it, in SCSS**. There are no lists of
  shades beside it, as there are on 20. Every class drawn from a color index is compiled from it:
  - the color picker's swatches (`o_colorlist_item_color_N`, `colorlist.scss`);
  - tags (`o_tag_color_N`, `tags_list.scss`) and badges (`o_badge_color_N`, `badge.scss`), whose
    background is `adjust-color(color, $lightness: 25%, $saturation: 15%)` and text
    `adjust-color(color, $lightness: -40%, $saturation: -15%)`;
  - kanban color bands (`utils.scss`, `kanban_record.scss`) and the kanban color picker;
  - calendars, through `$o-colors-complete`, which joins `$o-colors` to Odoo's secondary list
    (`calendar_renderer.scss` and its popovers), and Enterprise's Gantt;
  - the website's `o_color_N` (`website.scss`), Project's, Time Off's, Work Entries', Hierarchy's,
    and Point of Sale's own tags, which use other `adjust-color` amounts.

  Enterprise's dark mode builds its own `$o-colors` in
  `web_enterprise/static/src/scss/secondary_variables.dark.scss`, by darkening each color of
  `$o-colors-original` (`saturate(mix(color, black, 50%), 60%)`), and draws tags, badges, and
  swatches from it with its own `*.dark.scss` files (`mix` with the view's background, and
  `adjust-color`).

- **The names**, in `ColorList.COLORS` (`web/static/src/core/colorlist/colorlist.js`), a static
  array of translated strings that every picker shows as the swatches' titles.

**So the module sets the two lists and nothing else.** A custom color is drawn the way Odoo draws
its own, by Odoo's own formulas, in every one of those places, in light mode and in dark, because
what it changes is the input of those formulas. No shade is computed here. (Odoo 20 keeps three
lists of shades chosen by hand, which its module has to feed; 19 has no counterpart, and we do not
reimplement what core lacks.)

### The stylesheets

Odoo compiles SCSS when it builds a bundle, from files and from attachments: an `ir.asset` record
can name an attachment's URL as a path, which is how website saves the stylesheets its editor
customizes (`website.assets.save_asset`). That part is `base`'s, so this module does the same
without depending on website.

Whenever a custom color changes, `_update_stylesheets()` writes two SCSS files as attachments, at
`/_custom/vmk_colorlist_colors/colors.scss` and `colors.dark.scss`, and two `ir.asset` records
putting them in the bundles:

- **The light one goes first in `web._assets_primary_variables`** (`prepend`), and sets `$o-colors`
  `!default`. Odoo's own value is `!default` as well and comes later, in
  `web._assets_secondary_variables`, so ours, set before it, stands: in the backend, in the
  website's frontend bundles, which include the same variables, and everywhere else that compiles
  them. `$o-colors-complete`, defined after it, follows. Nothing of core's is replaced or patched.
- **The dark one goes just before it in `web.dark_mode_variables`**, a bundle only Enterprise has.
  Enterprise's dark variables are not set the same way: `$o-colors` there is built by appending each
  color of `$o-colors-original`, darkened, to an empty list. Our light stylesheet, being first,
  would have set `$o-colors` already, and Enterprise would append its twelve to our twelve. So the
  dark stylesheet sets `$o-colors-original`, with the custom colors in place, and sets `$o-colors`
  to an empty list; the light stylesheet's value is `!default` too, so in the dark bundle it leaves
  it empty for Enterprise to fill. **A custom color goes into the dark mode as an original**, so
  Enterprise darkens it as it does its own: the color you pick is not the one the dark mode draws,
  exactly as Odoo's own light colors are not what its dark mode draws. `tests/test_colors.py`
  compiles both bundles and checks there are still twelve colors.

Both files hold all twelve colors: Odoo's for the slots nobody changed, from `models/palette.py`,
which keeps a copy of Odoo's values (the first dark original is Sass, `lighten(#000, 46.7%)`, and is
written as Odoo writes it). `tests/test_palette.py` reads Odoo's SCSS and fails if Odoo changes
them, rather than letting an update mix our copy with its new values. When no color is custom, both
attachments and both asset records are deleted, and Odoo compiles exactly as it would without the
module. An `uninstall_hook` deletes them too: they are records the module made at run time, not its
data, so uninstalling would otherwise leave the custom colors in place with nothing to change them
back.

Writing an attachment that a bundle already names does not change the bundle's list of files, which
is what Odoo caches the bundle by, so the module clears the `assets` cache, as website does when it
saves a customized stylesheet.

### No color

Slot 0 is Odoo's "No color". Odoo's picker draws it as an empty circle whatever its color, and Odoo
gives it a meaning of its own: an event tag without a color is not shown on the website. So it stays
Odoo's, color and name. Its record exists like the others, and the stylesheets and the session carry
it, but the list leaves it out (the action's domain), and `write()` refuses any change to it, with a
message saying why, except a reset writing its own name back.

### The names

Each record's name is an ordinary translatable field, which the module's data fills with Odoo's
name. Its translations are in our own catalogues, as core's wording copied from `web`'s, so a
language activated later gets its names as any module's data does. The data is `noupdate`, so an
update keeps a name someone changed. Core leaves two names untranslated in Catalan, “Almond” and
“Teal”; ours has “Ametlla” and “Verd blavós”.

The same twelve names are also Python terms of the module (`palette.TRANSLATED_NAMES`, one catalogue
entry with both references), which is how `_odoo_names()` knows the default in any language, for the
reset and for telling a renamed color from an untouched one. Odoo's own names are JavaScript terms
of `web`, which Python's `_()` does not read.

All twelve names reach the web client in the session, in the user's language
(`ir.http.session_info`, `models/ir_http.py`), and `static/src/colorlist.js` writes them into
`ColorList.COLORS` when the backend loads, so every picker shows the names the list shows, including
the two Catalan ones core lacks. It changes the array in place rather than replacing it: the kanban
record takes `const { COLORS } = ColorList` when its module loads, and would keep the old array.

### Translations

The module's own name and summary are `ir.module.module` records whose xmlid belongs to `base`
(`base.module_vmk_colorlist_colors`). Odoo 19's `i18n export` does not write them, so they are kept
in the POT by hand, one entry for the name sharing its msgid with the model's own, as the sibling
modules do. `tests/test_translations.py` fails if the POT loses either entry, which would otherwise
leave the name in English in a translated database without a word. Terms core already translates are
taken in core's wording. Odoo's _Slot_ is _Espacio_ and _Ranura_, for an event's time slot; a
color's slot is its position in the list, so _Posición_ and _Posició_.

### Testing

`tests/test_palette.py` holds the copy of Odoo's values to Odoo's own files, and checks that Odoo
still derives its shades from `$o-colors` alone. `tests/test_colors.py` checks the records, their
access, both stylesheets and their asset records as colors change and reset, the compiled bundles,
and the names in the session in two languages. **It also compiles the backend bundle, and
Enterprise's dark one, with a slot given another slot's color, and requires every rule drawn for it
(tag, badge, swatch, kanban band, calendar) to equal that other slot's, declaration for
declaration**: a color of ours is drawn exactly as core draws its own, shades included.
`tests/test_tours.py` drives the list from General Settings, the reset button, and a contact tag's
color picker, whose swatch must carry the new name and be drawn in the new color.
