# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from datetime import timedelta
from unittest.mock import patch

from odoo import fields
from odoo.tests import tagged

from odoo.addons.vmk_mass_mailing_double_optin.models.vmk_mailing_consent_log import (
    CONTEXT_PROVEN,
)

from .common import DoubleOptInCommon


@tagged("post_install", "-at_install")
class TestConfirmation(DoubleOptInCommon):
    # ------------------------------------------------------------
    # Who has to confirm
    # ------------------------------------------------------------

    def test_visitor_subscription_awaits_confirmation(self):
        sub = self._subscribe_as_visitor("ana@example.com", self.list_doi)
        self.assertEqual(sub.vmk_confirmation_state, "pending")
        self.assertTrue(sub.vmk_confirmation_requested)

        mail = self._mails("ana@example.com")
        self.assertEqual(len(mail), 1)
        self.assertEqual(mail.subject, "Confirm your subscription to VMK Newsletter")
        self.assertIn(sub._vmk_confirmation_url().split("/mailing/")[1], mail.body_html)
        self.assertIn("This link is valid for 7 days.", mail.body_html)

        log = self._logs("ana@example.com")
        self.assertEqual(log.mapped("action"), ["requested"])
        self.assertEqual(log.source, "website")
        self.assertEqual(log.user_id, self.public_user)
        self.assertEqual(log.list_id, self.list_doi)
        self.assertEqual(log.list_name, "VMK Newsletter")

    def test_user_subscription_needs_no_confirmation(self):
        contact = self.env["mailing.contact"].with_user(self.marketer).create(
            {"name": "Bea", "email": "bea@example.com", "list_ids": [(6, 0, self.list_doi.ids)]}
        )
        sub = contact.subscription_ids
        self.assertFalse(sub.vmk_confirmation_state)
        self.assertFalse(self._mails("bea@example.com"))
        log = self._logs("bea@example.com")
        self.assertEqual(log.mapped("action"), ["subscribed"])
        self.assertEqual(log.source, "backend")
        self.assertEqual(log.user_id, self.marketer)

    def test_list_without_double_optin(self):
        sub = self._subscribe_as_visitor("cai@example.com", self.list_plain)
        self.assertFalse(sub.vmk_confirmation_state)
        self.assertFalse(self._mails("cai@example.com"))
        self.assertEqual(self._logs("cai@example.com").mapped("action"), ["subscribed"])

    def test_contact_without_email(self):
        env = self._visitor_env()
        contact = env["mailing.contact"].create({"name": "Phone Only"})
        sub = env["mailing.subscription"].create(
            {"contact_id": contact.id, "list_id": self.list_doi.id}
        )
        self.assertFalse(sub.vmk_confirmation_state)

    def test_list_ids_from_website_form(self):
        """Core's form builder creates the contact with `list_ids`, which the
        ORM writes straight into the subscription table."""
        env = self._visitor_env()
        contact = env["mailing.contact"].create(
            {"name": "Dan", "email": "dan@example.com", "list_ids": [(6, 0, self.list_doi.ids)]}
        )
        self.assertEqual(contact.subscription_ids.vmk_confirmation_state, "pending")
        self.assertEqual(len(self._mails("dan@example.com")), 1)
        self.assertEqual(self._logs("dan@example.com").mapped("action"), ["requested"])

    def test_list_ids_write_adds_and_removes(self):
        contact = self.env["mailing.contact"].create({"name": "Eli", "email": "eli@example.com"})
        contact.write({"list_ids": [(4, self.list_plain.id)]})
        contact.write({"list_ids": [(3, self.list_plain.id)]})
        self.assertFalse(contact.subscription_ids)
        logs = self._logs("eli@example.com")
        self.assertEqual(logs.mapped("action"), ["subscribed", "removed"])
        self.assertEqual(logs.mapped("list_id"), self.list_plain)

    def test_mailing_link_needs_no_confirmation(self):
        sub = self._subscribe_as_visitor(
            "fay@example.com", self.list_doi, **{CONTEXT_PROVEN: True}
        )
        self.assertFalse(sub.vmk_confirmation_state)
        log = self._logs("fay@example.com")
        self.assertEqual(log.mapped("action"), ["subscribed"])
        self.assertEqual(log.source, "email_link")

    def test_import_needs_no_confirmation(self):
        contact = self.env["mailing.contact"].with_context(import_file=True).create(
            {"name": "Gil", "email": "gil@example.com", "list_ids": [(6, 0, self.list_doi.ids)]}
        )
        self.assertFalse(contact.subscription_ids.vmk_confirmation_state)
        self.assertEqual(self._logs("gil@example.com").source, "import")

    def test_resubscribing_on_the_website_asks_again(self):
        contact = self.env["mailing.contact"].create(
            {"name": "Hal", "email": "hal@example.com", "list_ids": [(6, 0, self.list_doi.ids)]}
        )
        sub = contact.subscription_ids
        visitor_sub = sub.with_env(self._visitor_env())
        visitor_sub.opt_out = True
        visitor_sub.opt_out = False
        self.assertEqual(sub.vmk_confirmation_state, "pending")
        self.assertEqual(len(self._mails("hal@example.com")), 1)
        self.assertEqual(
            self._logs("hal@example.com").mapped("action"),
            ["subscribed", "unsubscribed", "requested"],
        )

    def test_a_second_request_soon_after_sends_nothing(self):
        sub = self._subscribe_as_visitor("ida@example.com", self.list_doi)
        token = sub._vmk_confirmation_token()
        sub.opt_out = True
        self.assertFalse(sub.vmk_confirmation_state)
        sub.with_env(self._visitor_env()).opt_out = False
        self.assertEqual(sub.vmk_confirmation_state, "pending")
        self.assertEqual(len(self._mails("ida@example.com")), 1)
        self.assertEqual(sub._vmk_confirmation_token(), token, "the first link still works")

    # ------------------------------------------------------------
    # Confirming
    # ------------------------------------------------------------

    def test_confirm(self):
        sub = self._subscribe_as_visitor("jo@example.com", self.list_doi)
        sub.with_env(self._visitor_env(**{CONTEXT_PROVEN: True}))._vmk_confirm()
        self.assertEqual(sub.vmk_confirmation_state, "confirmed")
        self.assertTrue(sub.vmk_confirmation_date)
        log = self._logs("jo@example.com")
        self.assertEqual(log.mapped("action"), ["requested", "confirmed"])
        self.assertEqual(log[1].source, "email_link")

    def test_token(self):
        sub = self._subscribe_as_visitor("kim@example.com", self.list_doi)
        token = sub._vmk_confirmation_token()
        self.assertTrue(sub._vmk_check_confirmation_token(token))
        tampered = token[:-1] + ("1" if token[-1] == "0" else "0")
        self.assertFalse(sub._vmk_check_confirmation_token(tampered))
        self.assertFalse(sub._vmk_check_confirmation_token(None))
        other = self._subscribe_as_visitor("lou@example.com", self.list_doi)
        self.assertFalse(other._vmk_check_confirmation_token(token))

        sub.contact_id.email = "kim.new@example.com"
        self.assertFalse(sub._vmk_check_confirmation_token(token), "the address changed")

    def test_a_new_request_replaces_the_link(self):
        sub = self._subscribe_as_visitor("max@example.com", self.list_doi)
        token = sub._vmk_confirmation_token()
        later = fields.Datetime.now() + timedelta(minutes=1)
        with patch.object(fields.Datetime, "now", return_value=later):
            sub.with_user(self.marketer).action_vmk_request_confirmation()
        self.assertFalse(sub._vmk_check_confirmation_token(token))
        self.assertEqual(len(self._mails("max@example.com")), 2)

    def test_requesting_confirmation_of_an_existing_subscriber(self):
        contact = self.env["mailing.contact"].create(
            {"name": "Ned", "email": "ned@example.com", "list_ids": [(6, 0, self.list_plain.ids)]}
        )
        contact.subscription_ids.with_user(self.marketer).action_vmk_request_confirmation()
        self.assertEqual(contact.subscription_ids.vmk_confirmation_state, "pending")
        self.assertEqual(len(self._mails("ned@example.com")), 1)

    def test_link_expires(self):
        sub = self._subscribe_as_visitor("ola@example.com", self.list_doi)
        self.assertFalse(sub._vmk_confirmation_expired())
        sub.vmk_confirmation_requested = fields.Datetime.now() - timedelta(days=8)
        self.assertTrue(sub._vmk_confirmation_expired())

    # ------------------------------------------------------------
    # Sending
    # ------------------------------------------------------------

    def _mailing(self, *lists):
        return self.env["mailing.mailing"].create(
            {
                "subject": "VMK News",
                "body_html": "<p>News</p>",
                "mailing_model_id": self.env.ref("mass_mailing.model_mailing_list").id,
                "contact_list_ids": [(6, 0, [mailing_list.id for mailing_list in lists])],
            }
        )

    def test_mailings_skip_those_awaiting_confirmation(self):
        sub = self._subscribe_as_visitor("pia@example.com", self.list_doi)
        mailing = self._mailing(self.list_doi)
        self.assertIn("pia@example.com", mailing._get_opt_out_list())
        sub._vmk_confirm()
        self.assertNotIn("pia@example.com", mailing._get_opt_out_list())

    def test_a_subscription_to_another_list_of_the_mailing_still_counts(self):
        self._subscribe_as_visitor("quinn@example.com", self.list_doi)
        self.env["mailing.contact"].create(
            {"name": "Quinn", "email": "quinn@example.com", "list_ids": [(6, 0, self.list_plain.ids)]}
        )
        self.assertNotIn("quinn@example.com", self._mailing(self.list_doi, self.list_plain)._get_opt_out_list())
        self.assertIn("quinn@example.com", self._mailing(self.list_doi)._get_opt_out_list())

    def test_sending_cancels_the_mail_to_those_awaiting_confirmation(self):
        self._subscribe_as_visitor("ray@example.com", self.list_doi)
        self.env["mailing.contact"].create(
            {"name": "Sam", "email": "sam@example.com", "list_ids": [(6, 0, self.list_doi.ids)]}
        )
        mailing = self._mailing(self.list_doi)
        mailing.action_send_mail()
        traces = {trace.email: trace for trace in mailing.mailing_trace_ids}
        self.assertEqual(traces["ray@example.com"].trace_status, "cancel")
        self.assertEqual(traces["ray@example.com"].failure_type, "mail_optout")
        self.assertNotEqual(traces["sam@example.com"].trace_status, "cancel")

    # ------------------------------------------------------------
    # Expiry
    # ------------------------------------------------------------

    def test_expiry_removes_unconfirmed_subscriptions(self):
        old = self._subscribe_as_visitor("tia@example.com", self.list_doi)
        recent = self._subscribe_as_visitor("uma@example.com", self.list_doi)
        kept_contact = self.env["mailing.contact"].create(
            {"name": "Val", "email": "val@example.com", "list_ids": [(6, 0, self.list_plain.ids)]}
        )
        old_on_kept = self.env["mailing.subscription"].with_env(self._visitor_env()).create(
            {"contact_id": kept_contact.id, "list_id": self.list_doi.id}
        )
        eight_days_ago = fields.Datetime.now() - timedelta(days=8)
        (old | old_on_kept).write({"vmk_confirmation_requested": eight_days_ago})
        old_contact = old.contact_id

        self.env["mailing.subscription"]._cron_vmk_expire_confirmations()

        self.assertFalse(old.exists())
        self.assertFalse(old_on_kept.exists())
        self.assertTrue(recent.exists())
        self.assertFalse(old_contact.exists(), "created by the website for that signup alone")
        self.assertTrue(kept_contact.exists(), "subscribed to another list")
        self.assertEqual(self._logs("tia@example.com").mapped("action"), ["requested", "expired"])
        self.assertEqual(self._logs("tia@example.com")[1].source, "system")
