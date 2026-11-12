# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

import re

from odoo.tests.common import TransactionCase, tagged
from odoo.tools import file_open

from odoo.addons.vmk_colorlist_colors.models import palette


def scss_list(source, name):
    """The values of an SCSS list variable, as Odoo writes them."""
    match = re.search(rf"^\${re.escape(name)}:(.*?)!default;", source, re.M | re.S)
    return tuple(re.findall(r"#[0-9a-fA-F]{6}", match.group(1))) if match else None


@tagged("post_install", "-at_install")
class TestPalette(TransactionCase):
    """Our copy of Odoo's defaults against Odoo's own files, so an Odoo
    update that changes them fails here instead of mixing old and new."""

    def test_light_defaults_are_odoos(self):
        with file_open("web/static/src/scss/primary_variables.scss") as f:
            source = f.read()
        for name, ours in (
            ("o-colors", palette.COLORS),
            ("o-colors-border", palette.BORDER),
            ("o-colors-bg-subtle", palette.BG_SUBTLE),
            ("o-colors-text-emphasis", palette.TEXT_EMPHASIS),
        ):
            with self.subTest(variable=name):
                self.assertEqual(tuple(c.lower() for c in scss_list(source, name)), ours)

    def test_dark_defaults_are_enterprises(self):
        try:
            with file_open("web_enterprise/static/src/scss/primary_variables.dark.scss") as f:
                source = f.read()
        except FileNotFoundError:
            self.skipTest("Enterprise, which has the dark mode, is not on the addons path.")
        for name, ours in (
            ("o-colors-original", palette.DARK_COLORS),
            ("o-colors-border", palette.DARK_BORDER),
            ("o-colors-bg-subtle", palette.DARK_BG_SUBTLE),
            ("o-colors-text-emphasis", palette.DARK_TEXT_EMPHASIS),
        ):
            with self.subTest(variable=name):
                self.assertEqual(tuple(c.lower() for c in scss_list(source, name)), ours)

    def test_names_are_odoos(self):
        with file_open("web/static/src/core/colorlist/colorlist.js") as f:
            source = f.read()
        names = re.search(r"static COLORS = \[(.*?)\];", source, re.S).group(1)
        self.assertEqual(tuple(re.findall(r'_t\("([^"]+)"\)', names)), palette.NAMES)

    def test_round_trip(self):
        for color in palette.COLORS + palette.DARK_BORDER:
            with self.subTest(color=color):
                self.assertEqual(palette.from_oklch(*palette.to_oklch(color)), color)

    def test_shades_follow_odoos_roles(self):
        """Odoo's own colors, put through shades(), come out with the
        lightness of Odoo's own shades, and their hue where they have one."""
        for dark, defaults in (
            (False, (palette.BORDER, palette.BG_SUBTLE, palette.TEXT_EMPHASIS)),
            (True, (palette.DARK_BORDER, palette.DARK_BG_SUBTLE, palette.DARK_TEXT_EMPHASIS)),
        ):
            for slot, color in enumerate(palette.COLORS):
                ours = palette.shades(color, dark=dark)
                for role, odoo in zip(("border", "bg_subtle", "text_emphasis"), defaults):
                    with self.subTest(dark=dark, slot=slot, role=role):
                        lightness, _chroma, _hue = palette.to_oklch(ours[role])
                        odoo_lightness, _chroma, _hue = palette.to_oklch(odoo[slot])
                        self.assertAlmostEqual(lightness, odoo_lightness, delta=0.06)

    def test_out_of_gamut_keeps_lightness_and_hue(self):
        lightness, chroma, hue = 0.9, 0.3, 140.0
        color = palette.from_oklch(lightness, chroma, hue)
        got_lightness, got_chroma, got_hue = palette.to_oklch(color)
        self.assertAlmostEqual(got_lightness, lightness, delta=0.01)
        self.assertAlmostEqual(got_hue, hue, delta=2)
        self.assertLess(got_chroma, chroma)
