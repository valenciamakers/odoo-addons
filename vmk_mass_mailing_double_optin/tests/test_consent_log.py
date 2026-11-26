# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import DoubleOptInCommon


@tagged("post_install", "-at_install")
class TestConsentLog(DoubleOptInCommon):
    def _contact(self, email, *lists):
        return self.env["mailing.contact"].create(
            {"name": email, "email": email, "list_ids": [(6, 0, [ml.id for ml in lists])]}
        )

    def test_unsubscribing_and_the_reason(self):
        contact = self._contact("ann@example.com", self.list_plain)
        reason = self.env["mailing.subscription.optout"].create({"name": "VMK Too Often"})
        visitor_sub = contact.subscription_ids.with_env(self._visitor_env())
        visitor_sub.opt_out = True
        # Core's page asks for the reason afterwards, in a second request.
        visitor_sub.opt_out_reason_id = reason

        logs = self._logs("ann@example.com")
        self.assertEqual(logs.mapped("action"), ["subscribed", "unsubscribed", "reason"])
        self.assertEqual(logs[1].source, "website")
        self.assertFalse(logs[1].reason)
        self.assertEqual(logs[2].reason, "VMK Too Often")

    def test_unsubscribing_with_a_reason_at_once(self):
        contact = self._contact("ben@example.com", self.list_plain)
        reason = self.env["mailing.subscription.optout"].create({"name": "VMK Not Relevant"})
        contact.subscription_ids.opt_out_reason_id = reason  # core sets opt_out from it
        self.assertTrue(contact.subscription_ids.opt_out)
        self.assertEqual(
            self._logs("ben@example.com").mapped("reason"), [False, "VMK Not Relevant"]
        )

    def test_deleting_a_contact_logs_each_subscription(self):
        contact = self._contact("cal@example.com", self.list_doi, self.list_plain)
        contact.unlink()
        removed = self._logs("cal@example.com").filtered(lambda log: log.action == "removed")
        self.assertEqual(removed.list_id, self.list_doi | self.list_plain)
        self.assertFalse(removed.contact_id, "the line outlives the contact")

    def test_deleting_a_list_logs_its_subscriptions(self):
        self._contact("dee@example.com", self.list_plain)
        self.list_plain.unlink()
        removed = self._logs("dee@example.com").filtered(lambda log: log.action == "removed")
        self.assertEqual(len(removed), 1)
        self.assertFalse(removed.list_id)
        self.assertEqual(removed.list_name, "VMK Plain List", "the line keeps the list's name")

    def test_deleting_a_subscription(self):
        contact = self._contact("eve@example.com", self.list_plain)
        contact.subscription_ids.unlink()
        self.assertEqual(self._logs("eve@example.com").mapped("action"), ["subscribed", "removed"])

    def test_blacklist(self):
        Blacklist = self.env["mail.blacklist"]
        Blacklist._add("Fox <fox@example.com>")
        Blacklist._add("fox@example.com")  # already there: nothing new
        Blacklist._remove("fox@example.com")
        Blacklist._add("fox@example.com")
        self.assertEqual(
            self._logs("fox@example.com").mapped("action"),
            ["blacklisted", "unblacklisted", "blacklisted"],
        )
        Blacklist.search([("email", "=", "fox@example.com")]).unlink()
        self.assertEqual(self._logs("fox@example.com")[-1].action, "unblacklisted")

    def test_unblacklisting_an_unknown_address_logs_nothing(self):
        self.env["mail.blacklist"]._remove("gus@example.com")
        self.assertFalse(self._logs("gus@example.com"))

    def test_lines_cannot_be_changed(self):
        self._contact("hana@example.com", self.list_plain)
        log = self._logs("hana@example.com")
        with self.assertRaises(UserError):
            log.write({"action": "unsubscribed"})
        with self.assertRaises(UserError):
            log.sudo().write({"email": "someone@example.com"})

    def test_no_request_no_visitor_details(self):
        self._subscribe_as_visitor("ivy@example.com", self.list_doi)
        log = self._logs("ivy@example.com")
        self.assertFalse(log.ip_address or log.user_agent or log.url)
