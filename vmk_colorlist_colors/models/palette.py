# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

"""Odoo's twelve colors.

The defaults are copied from Odoo 19's own sources, which only set them as
SCSS variables: `$o-colors` in `web/static/src/scss/secondary_variables.scss`
(light), and `$o-colors-original` in
`web_enterprise/static/src/scss/secondary_variables.dark.scss` (Enterprise's
dark mode, which darkens each into its own `$o-colors`), with the names from
`web/static/src/core/colorlist/colorlist.js`. `tests/test_palette.py` reads
those files and fails if Odoo changes them.

Odoo 19 derives everything else from these lists, in SCSS: a tag's and a
badge's background and text with `adjust-color`, a kanban card's band, a
calendar's colors, and Enterprise's dark mode with `mix` and `saturate`. So
this module only supplies the lists, and Odoo's own stylesheets draw a custom
color the way they draw Odoo's: there are no shades to compute here.
"""

from odoo.tools import LazyTranslate

_lt = LazyTranslate(__name__)

# The names, translated by our own catalogues: core's translations of them,
# copied, and ours where core has none (Catalan has no Almond or Teal).
TRANSLATED_NAMES = (
    _lt("No color"),
    _lt("Red"),
    _lt("Orange"),
    _lt("Yellow"),
    _lt("Cyan"),
    _lt("Purple"),
    _lt("Almond"),
    _lt("Teal"),
    _lt("Blue"),
    _lt("Raspberry"),
    _lt("Green"),
    _lt("Violet"),
)
NAMES = tuple(name._source for name in TRANSLATED_NAMES)

COLORS = (
    "#a2a2a2", "#ee2d2d", "#dc8534", "#e8bb1d", "#5794dd", "#9f628f",
    "#db8865", "#41a9a2", "#304be0", "#ee2f8a", "#61c36e", "#9872e6",
)

# Enterprise's dark mode starts from a list of its own, which it darkens into
# $o-colors itself (saturate(mix(color, black, 50%), 60%)). The first is
# written as Odoo writes it, a Sass expression.
DARK_ORIGINAL = (
    "lighten(#000, 46.7%)", "#e74e4e", "#f4b660", "#f7cd1f", "#6cedeb", "#8d5482",
    "#f07b50", "#2c8397", "#475577", "#dc0457", "#30c381", "#9365b8",
)
