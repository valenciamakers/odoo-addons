# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

import re
from datetime import timedelta

from odoo import fields
from odoo.tests import HttpCase, tagged

from .common import DoubleOptInCommon

CSRF = re.compile(r'name="csrf_token" value="([^"]+)"')
INVALID = "This link has expired or is not valid."


@tagged("post_install", "-at_install")
class TestConfirmationPage(HttpCase, DoubleOptInCommon):
    def setUp(self):
        super().setUp()
        self.subscription = self._subscribe_as_visitor("pat@example.com", self.list_doi)
        self.url = self.subscription._vmk_confirmation_url(self.base_url())

    def _post(self, url, token):
        page = self.url_open(url)
        csrf = CSRF.search(page.text).group(1)
        return self.url_open(url.split("?")[0], data={"csrf_token": csrf, "token": token})

    def test_opening_the_link_confirms_nothing(self):
        """Mail scanners open links: only the button confirms."""
        page = self.url_open(self.url)
        self.assertEqual(page.status_code, 200)
        self.assertIn("Confirm your subscription to VMK Newsletter for pat@example.com.", page.text)
        self.assertEqual(self.subscription.vmk_confirmation_state, "pending")

    def test_the_button_confirms(self):
        token = self.subscription._vmk_confirmation_token()
        page = self._post(self.url, token)
        self.assertEqual(page.status_code, 200)
        self.assertIn("You are now subscribed to VMK Newsletter from", page.text)
        self.assertEqual(self.subscription.vmk_confirmation_state, "confirmed")

        log = self._logs("pat@example.com")[-1]
        self.assertEqual(log.action, "confirmed")
        self.assertEqual(log.source, "email_link")
        self.assertEqual(log.ip_address, "127.0.0.1")
        self.assertTrue(log.user_agent)
        self.assertTrue(log.url.endswith(f"/mailing/subscription/{self.subscription.id}/confirm"))
        self.assertNotIn("token", log.url)

        again = self.url_open(self.url)
        self.assertIn("You are now subscribed to VMK Newsletter", again.text)

    def test_posting_without_the_csrf_token_is_refused(self):
        self.url_open(
            self.url.split("?")[0], data={"token": self.subscription._vmk_confirmation_token()}
        )
        self.assertEqual(self.subscription.vmk_confirmation_state, "pending")

    def test_a_wrong_token_or_subscription_gets_the_same_page(self):
        token = self.subscription._vmk_confirmation_token()
        for url in (
            f"/mailing/subscription/{self.subscription.id}/confirm?token=x{token[1:]}",
            f"/mailing/subscription/{self.subscription.id}/confirm",
            f"/mailing/subscription/{self.subscription.id + 1000}/confirm?token={token}",
        ):
            with self.subTest(url=url):
                self.assertIn(INVALID, self.url_open(url).text)
        self.assertEqual(self.subscription.vmk_confirmation_state, "pending")

    def test_an_expired_link(self):
        self.subscription.vmk_confirmation_requested -= timedelta(days=8)
        url = self.subscription._vmk_confirmation_url(self.base_url())
        self.assertIn(INVALID, self.url_open(url).text)

    def test_an_unsubscribed_address(self):
        self.subscription.opt_out = True
        self.assertIn(INVALID, self.url_open(self.url).text)

    def test_core_subscription_page_with_a_mailing_token_needs_no_confirmation(self):
        contact = self.env["mailing.contact"].create(
            {"name": "Rae", "email": "rae@example.com", "list_ids": [(6, 0, self.list_plain.ids)]}
        )
        mailing = self.env["mailing.mailing"].create(
            {
                "subject": "VMK News",
                "body_html": "<p>News</p>",
                "mailing_model_id": self.env.ref("mass_mailing.model_mailing_list").id,
                "contact_list_ids": [(6, 0, self.list_plain.ids)],
            }
        )
        self.make_jsonrpc_request(
            "/mailing/list/update",
            {
                "mailing_id": mailing.id,
                "document_id": contact.id,
                "email": "rae@example.com",
                "hash_token": mailing._generate_mailing_recipient_token(
                    contact.id, "rae@example.com"
                ),
                "lists_optin_ids": (self.list_plain | self.list_doi).ids,
            },
        )
        subscription = contact.subscription_ids.filtered(
            lambda sub: sub.list_id == self.list_doi
        )
        self.assertTrue(subscription)
        self.assertFalse(subscription.vmk_confirmation_state)
        log = self._logs("rae@example.com")[-1]
        self.assertEqual((log.action, log.source), ("subscribed", "email_link"))
        self.assertNotIn("hash_token", log.url or "")
