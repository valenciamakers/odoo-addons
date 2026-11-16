# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo.tests import HttpCase, tagged

from .common import DoubleOptInCommon


@tagged("post_install", "-at_install")
class TestTours(HttpCase, DoubleOptInCommon):
    def test_confirm_from_the_email_link(self):
        subscription = self._subscribe_as_visitor("tour@example.com", self.list_doi)
        url = subscription._vmk_confirmation_url(self.base_url())
        self.start_tour(url.removeprefix(self.base_url()), "vmk_mass_mailing_double_optin_confirm")
        self.assertEqual(subscription.vmk_confirmation_state, "confirmed")

    def test_resend_from_the_contact_form(self):
        """As an email marketing user, the least role that reaches the form."""
        subscription = self._subscribe_as_visitor("tour.backend@example.com", self.list_doi)
        self.start_tour(
            f"/odoo/mailing.contact/{subscription.contact_id.id}",
            "vmk_mass_mailing_double_optin_backend",
            login=self.marketer.login,
        )
        self.assertEqual(len(self._mails("tour.backend@example.com")), 2)
        self.assertEqual(
            self._logs("tour.backend@example.com").mapped("source"), ["website", "backend"]
        )

    def test_request_confirmation_from_the_recipients(self):
        contact = self.env["mailing.contact"].with_user(self.marketer).create(
            {
                "name": "Tour Bulk",
                "email": "tour.bulk@example.com",
                "list_ids": [(6, 0, self.list_doi.ids)],
            }
        )
        self.start_tour(
            f"/odoo/mailing.list/{self.list_doi.id}",
            "vmk_mass_mailing_double_optin_request",
            login=self.marketer.login,
        )
        self.assertEqual(contact.subscription_ids.vmk_confirmation_state, "pending")
        self.assertEqual(len(self._mails("tour.bulk@example.com")), 1)
