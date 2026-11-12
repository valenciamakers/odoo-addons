# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

"""Odoo's twelve colors, and the shades derived from each.

The defaults are copied from Odoo 20's own sources, which only set them as
SCSS variables: `web/static/src/scss/primary_variables.scss` (light) and
`web_enterprise/static/src/scss/primary_variables.dark.scss` (Enterprise's
dark mode), with the names from `web/static/src/core/colorlist/colorlist.js`.
`tests/test_palette.py` reads those files and fails if Odoo changes them.

Each color has three shades for tags and badges: a border, a light
background, and a dark text color. Odoo picked its own in OKLCH, keeping each
color's hue and giving every shade of a role nearly the same lightness, with
its chroma capped. `shades()` does the same for any color, from the
lightness and cap Odoo's own values show for each role.
"""

import math

NAMES = (
    "No color",
    "Red",
    "Orange",
    "Yellow",
    "Cyan",
    "Purple",
    "Almond",
    "Teal",
    "Blue",
    "Raspberry",
    "Green",
    "Violet",
)

COLORS = (
    "#a2a2a2", "#ee2d2d", "#dc8534", "#e8bb1d", "#5794dd", "#9f628f",
    "#db8865", "#41a9a2", "#304be0", "#ee2f8a", "#61c36e", "#9872e6",
)

BORDER = (
    "#8f8f8f", "#d76a58", "#cc7724", "#c09910", "#179dc5", "#b271c6",
    "#af8563", "#17a49d", "#5d8ee4", "#d06792", "#4ca65a", "#8f7ede",
)
BG_SUBTLE = (
    "#d7d7d7", "#fedbd5", "#fedec5", "#f4dc9d", "#c2ecfe", "#ebcaf6",
    "#f2e1d4", "#aef4ee", "#c3d9fe", "#fec5d9", "#bae5bd", "#e4e1fe",
)
TEXT_EMPHASIS = (
    "#3d3d3d", "#6b1f15", "#5c3003", "#4c3b04", "#044457", "#542662",
    "#4d3827", "#034744", "#193a76", "#671d3f", "#044b18", "#3e2f72",
)

# Enterprise's dark mode starts from a list of its own, which it darkens into
# $o-colors itself (saturate(mix(color, black, 80%), 65%)), and has its own
# shades.
DARK_COLORS = (
    "#a2a2a2", "#ee2d2d", "#dc8534", "#8c700e", "#5794dd", "#986497",
    "#db8865", "#008278", "#304be0", "#ee2f8a", "#009345", "#9872e6",
)
DARK_BORDER = (
    "#b1b1b1", "#f8907e", "#ee9b56", "#d1ad41", "#37c2ef", "#d396e6",
    "#d1a888", "#1ccbc2", "#86b1fd", "#f28db4", "#75c77f", "#b0a2fd",
)
DARK_BG_SUBTLE = (
    "#2e2e2e", "#58271f", "#542d06", "#392c02", "#043e50", "#3d2046",
    "#463324", "#04413e", "#172d53", "#4a1b2f", "#0d3715", "#38305c",
)
DARK_TEXT_EMPHASIS = (
    "#d7d7d7", "#fec9bf", "#fecca6", "#eed592", "#a0e3fe", "#f1c5fe",
    "#ebd2bf", "#8eebe3", "#c3d9fe", "#fec5d9", "#b0e8b5", "#d6d1fe",
)

# Each role's OKLCH lightness, and the most chroma it takes, as Odoo's own
# shades have them: in light mode, borders at 0.65, backgrounds near 0.90,
# and text at 0.36; in dark, 0.76, near 0.32, and 0.88.
ROLES = {
    "border": (0.65, 0.14),
    "bg_subtle": (0.90, 0.055),
    "text_emphasis": (0.36, 0.11),
}
DARK_ROLES = {
    "border": (0.76, 0.13),
    "bg_subtle": (0.32, 0.075),
    "text_emphasis": (0.88, 0.09),
}


def _to_linear(channel):
    channel /= 255
    return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4


def _from_linear(channel):
    channel = 12.92 * channel if channel <= 0.0031308 else 1.055 * channel ** (1 / 2.4) - 0.055
    return channel * 255


def to_oklch(hex_color):
    """(lightness, chroma, hue in degrees) of a `#rrggbb` color."""
    r, g, b = (_to_linear(int(hex_color[i:i + 2], 16)) for i in (1, 3, 5))
    l = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
    m = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    lightness = 0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s
    a = 1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s
    b_ = 0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s
    return lightness, math.hypot(a, b_), math.degrees(math.atan2(b_, a)) % 360


def _to_rgb(lightness, chroma, hue):
    a = chroma * math.cos(math.radians(hue))
    b = chroma * math.sin(math.radians(hue))
    l = (lightness + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m = (lightness - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s = (lightness - 0.0894841775 * a - 1.2914855480 * b) ** 3
    return tuple(_from_linear(c) for c in (
        4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
        -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
        -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s,
    ))


def from_oklch(lightness, chroma, hue):
    """The `#rrggbb` color nearest an OKLCH one. A color outside sRGB loses
    chroma, keeping its lightness and hue, until it fits, as CSS's own gamut
    mapping does."""
    def fits(c):
        return all(-0.5 <= channel <= 255.5 for channel in _to_rgb(lightness, c, hue))

    if not fits(chroma):
        low, high = 0.0, chroma
        for _ in range(30):
            mid = (low + high) / 2
            low, high = (mid, high) if fits(mid) else (low, mid)
        chroma = low
    return "#" + "".join(
        f"{round(min(max(channel, 0), 255)):02x}" for channel in _to_rgb(lightness, chroma, hue)
    )


def shades(hex_color, dark=False):
    """A color's border, light background, and dark text shades, as a dict
    keyed by role, for light mode or Enterprise's dark one."""
    _lightness, chroma, hue = to_oklch(hex_color)
    roles = DARK_ROLES if dark else ROLES
    return {
        role: from_oklch(lightness, min(chroma, cap), hue)
        for role, (lightness, cap) in roles.items()
    }
