# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

import re

from odoo.tests.common import TransactionCase, tagged
from odoo.tools import file_open

from odoo.addons.vmk_colorlist_colors.models import palette

SASS_COLOR = re.compile(r"lighten\(#000, 46\.7%\)|#[0-9a-fA-F]{6}")


def scss_list(source, name):
    """The values of an SCSS list variable, as Odoo writes them."""
    match = re.search(rf"^\${re.escape(name)}:(.*?)!default;", source, re.M | re.S)
    return tuple(c.lower() for c in SASS_COLOR.findall(match.group(1))) if match else None


@tagged("post_install", "-at_install")
class TestPalette(TransactionCase):
    """Our copy of Odoo's defaults against Odoo's own files, so an Odoo
    update that changes them fails here instead of mixing old and new."""

    def test_light_defaults_are_odoos(self):
        with file_open("web/static/src/scss/secondary_variables.scss") as f:
            source = f.read()
        self.assertEqual(scss_list(source, "o-colors"), palette.COLORS)

    def test_dark_defaults_are_enterprises(self):
        try:
            with file_open("web_enterprise/static/src/scss/secondary_variables.dark.scss") as f:
                source = f.read()
        except FileNotFoundError:
            self.skipTest("Enterprise, which has the dark mode, is not on the addons path.")
        self.assertEqual(scss_list(source, "o-colors-original"), palette.DARK_ORIGINAL)
        # What Enterprise does with each original is what a custom color gets.
        self.assertIn("saturate(mix($-color, $o-black, 50%), 60%)", source)

    def test_names_are_odoos(self):
        with file_open("web/static/src/core/colorlist/colorlist.js") as f:
            source = f.read()
        names = re.search(r"static COLORS = \[(.*?)\];", source, re.S).group(1)
        self.assertEqual(tuple(re.findall(r'_t\("([^"]+)"\)', names)), palette.NAMES)

    def test_shades_are_still_derived_from_the_list_alone(self):
        """The module sets no shades, because on 18 Odoo draws a tag's and a
        swatch's from $o-colors with adjust-color. If a release gives them
        lists of their own, as Odoo 20 has, this module needs them too."""
        for path in (
            "web/static/src/core/tags_list/tags_list.scss",
            "web/static/src/core/colorlist/colorlist.scss",
        ):
            with file_open(path) as f:
                source = f.read()
            with self.subTest(path=path):
                self.assertIn("adjust-color(nth($o-colors, $size), $lightness: 25%, $saturation: 15%)", source)
                self.assertIn("adjust-color(nth($o-colors, $size), $lightness: -40%, $saturation: -15%)", source)
        for path in ("web/static/src/scss/primary_variables.scss", "web/static/src/scss/secondary_variables.scss"):
            with file_open(path) as f:
                self.assertNotIn("$o-colors-bg-subtle", f.read())
