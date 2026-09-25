# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo.tests import tagged

from ..models import email_sync
from .common import PartnerEmailCase

MAIL = """From: Alice Example <{sender}>
To: hello@example.org
Subject: {subject}
Message-ID: <{key}@example.com>
Content-Type: text/plain; charset=utf-8

Hello.
"""


@tagged("post_install", "-at_install")
class TestEmailSync(PartnerEmailCase):
    """Apps that copy a record's email onto its contact leave the primary alone.

    The app tests skip where the app is not installed; run them on a database that
    has CRM and Recruitment, and Helpdesk where Enterprise is available.
    """

    def _require(self, model):
        if model not in self.env:
            self.skipTest(f"{model} is not installed")

    def _mail(self, model, sender, subject):
        key = subject.lower().replace(" ", "-")
        message = MAIL.format(sender=sender, subject=subject, key=key)
        return self.env[model].browse(self.env["mail.thread"].message_process(model, message))

    # ------------------------------------------------------------
    # The patches themselves
    # ------------------------------------------------------------

    def test_every_installed_app_is_patched(self):
        for model, methods in email_sync.PATCHES.items():
            if model not in self.env:
                continue
            for name in methods:
                method = getattr(type(self.env[model]), name)
                self.assertTrue(getattr(method, email_sync.PATCHED, False), f"{model}.{name}")

    def test_installing_again_does_not_wrap_twice(self):
        email_sync.install(self.env)
        for model, methods in email_sync.PATCHES.items():
            if model not in self.env:
                continue
            for name in methods:
                origin = getattr(type(self.env[model]), name).origin
                self.assertFalse(getattr(origin, email_sync.PATCHED, False), f"{model}.{name}")

    def test_keep_primary_drops_only_an_additional_address(self):
        guarded = self.alice.with_context(**{email_sync.KEEP_PRIMARY: True})
        guarded.write({"email": "alice.work@example.com", "phone": "+34 600 000 001"})
        self.assertEqual(self.alice.email, "alice@example.com")
        self.assertEqual(self.alice.phone, "+34 600 000 001")
        guarded.write({"email": "alice.new@example.com"})
        self.assertEqual(self.alice.email, "alice.new@example.com")

    def test_without_the_flag_an_additional_address_can_still_be_made_primary(self):
        """Typing an additional address into the email field is the user's call."""
        self.alice.email = "alice.work@example.com"
        self.assertEqual(self.alice.email, "alice.work@example.com")

    # ------------------------------------------------------------
    # CRM
    # ------------------------------------------------------------

    def test_a_lead_from_an_additional_address_keeps_the_primary(self):
        self._require("crm.lead")
        lead = self._mail("crm.lead", "alice.work@example.com", "A lead")
        self.assertEqual(lead.partner_id, self.alice)
        self.assertEqual(lead.email_normalized, "alice.work@example.com")
        self.assertEqual(self.alice.email, "alice@example.com")
        self.assertFalse(lead.partner_email_update)

    def test_a_lead_with_a_new_address_still_updates_the_contact(self):
        self._require("crm.lead")
        lead = self.env["crm.lead"].create({"name": "A lead", "partner_id": self.alice.id})
        lead.email_from = "alice.new@example.com"
        self.assertEqual(self.alice.email, "alice.new@example.com")

    # ------------------------------------------------------------
    # Recruitment
    # ------------------------------------------------------------

    def test_an_application_from_an_additional_address_keeps_the_primary(self):
        self._require("hr.applicant")
        applicant = self._mail("hr.applicant", "alice.work@example.com", "An application")
        self.assertEqual(applicant.partner_id, self.alice)
        self.assertEqual(self.alice.email, "alice@example.com")

    def test_an_application_still_syncs_the_phone(self):
        self._require("hr.applicant")
        self.env["hr.applicant"].create(
            {
                "partner_name": "Alice Example",
                "partner_id": self.alice.id,
                "email_from": "alice.work@example.com",
                "partner_phone": "+34 600 000 002",
            }
        )
        self.assertEqual(self.alice.email, "alice@example.com")
        self.assertEqual(self.alice.phone, "+34 600 000 002")

    def test_an_application_with_a_new_address_still_updates_the_contact(self):
        self._require("hr.applicant")
        self.env["hr.applicant"].create(
            {
                "partner_name": "Alice Example",
                "partner_id": self.alice.id,
                "email_from": "alice.new@example.com",
            }
        )
        self.assertEqual(self.alice.email, "alice.new@example.com")

    # ------------------------------------------------------------
    # Helpdesk (Enterprise)
    # ------------------------------------------------------------

    def test_a_ticket_from_an_additional_address_keeps_the_primary(self):
        self._require("helpdesk.ticket")
        ticket = self.env["helpdesk.ticket"].create(
            {
                "name": "A ticket",
                "partner_id": self.alice.id,
                "partner_email": "alice.work@example.com",
            }
        )
        self.assertEqual(ticket.partner_email, "alice.work@example.com")
        self.assertEqual(self.alice.email, "alice@example.com")

    def test_a_ticket_with_a_new_address_still_updates_the_contact(self):
        self._require("helpdesk.ticket")
        ticket = self.env["helpdesk.ticket"].create({"name": "A ticket", "partner_id": self.alice.id})
        ticket.partner_email = "alice.new@example.com"
        self.assertEqual(self.alice.email, "alice.new@example.com")
