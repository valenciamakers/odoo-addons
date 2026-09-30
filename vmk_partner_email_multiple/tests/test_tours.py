# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestTours(HttpCase):
    """Drive the contact form, list, and autocomplete in a real browser."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.alice = cls.env["res.partner"].create(
            {
                "name": "Alice Example",
                "email": "alice@example.com",
                "vmk_email_ids": [
                    (0, 0, {"email": "alice.work@example.com", "label": "work"}),
                ],
            }
        )
        cls.bob = cls.env["res.partner"].create(
            {"name": "Bob Builder", "email": "bob@example.com"}
        )

    def _form_url(self, partner):
        return f"/odoo/action-base.action_partner_form/{partner.id}"

    def test_add_additional_email(self):
        self.start_tour(
            self._form_url(self.bob), "vmk_partner_email_multiple_add_tour", login="admin"
        )
        row = self.bob.vmk_email_ids
        self.assertEqual(row.mapped("email"), ["alice.billing@example.com"])
        self.assertEqual(row.label, "billing")
        self.assertEqual(row.email_normalized, "alice.billing@example.com")

    def test_swap_with_primary(self):
        self.start_tour(
            self._form_url(self.alice), "vmk_partner_email_multiple_swap_tour", login="admin"
        )
        self.alice.invalidate_recordset()
        self.assertEqual(self.alice.email, "alice.work@example.com")
        self.assertEqual(self.alice.vmk_email_ids.mapped("email"), ["alice@example.com"])
        self.assertFalse(self.alice.vmk_email_ids.label)

    def test_envelope_link(self):
        self.start_tour(
            self._form_url(self.alice), "vmk_partner_email_multiple_link_tour", login="admin"
        )

    def test_search_by_additional_email(self):
        self.start_tour(
            "/odoo/action-base.action_partner_form?view_type=list",
            "vmk_partner_email_multiple_search_tour",
            login="admin",
        )

    def test_many2one_autocomplete(self):
        self.start_tour(
            "/odoo/action-base.action_partner_form/new",
            "vmk_partner_email_multiple_autocomplete_tour",
            login="admin",
        )
