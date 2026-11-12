# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestTours(HttpCase):
    """Drive the list of colors, and a color picker elsewhere, in a browser."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["vmk.colorlist.color"].search([]).action_reset()
        cls.purple = cls.env.ref("vmk_colorlist_colors.color_5")

    def test_edit_from_settings(self):
        self.start_tour("/odoo/settings", "vmk_colorlist_colors_edit_tour", login="admin")
        self.assertEqual(self.purple.custom_color, "#7b2cbf")
        self.assertEqual(self.purple.name, "Brand")

    def test_reset_a_color(self):
        self.purple.write({"color": "#7b2cbf", "name": "Brand"})
        self.start_tour("/odoo/custom-colors", "vmk_colorlist_colors_reset_tour", login="admin")
        self.assertFalse(self.purple.is_custom)

    def test_a_picker_elsewhere_takes_the_name_and_color(self):
        self.purple.write({"color": "#7b2cbf", "name": "Brand"})
        self.env["res.partner.category"].create({"name": "VMK test tag", "color": 5})
        self.start_tour(
            "/odoo/action-base.action_partner_category_form",
            "vmk_colorlist_colors_picker_tour",
            login="admin",
        )
