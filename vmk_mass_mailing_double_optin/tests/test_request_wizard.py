# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo.exceptions import AccessError, UserError
from odoo.tests import Form, tagged
from odoo.tests.common import new_test_user

from .common import DoubleOptInCommon


@tagged("post_install", "-at_install")
class TestRequestWizard(DoubleOptInCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Contact = cls.env["mailing.contact"].with_user(cls.marketer)

        def added(email, *lists):
            return Contact.create(
                {"name": email, "email": email, "list_ids": [(6, 0, [ml.id for ml in lists])]}
            )

        cls.ana = added("ana.bulk@example.com", cls.list_doi, cls.list_plain)
        cls.ben = added("ben.bulk@example.com", cls.list_doi)
        cls.unsubscribed = added("unsub.bulk@example.com", cls.list_doi)
        cls.unsubscribed.subscription_ids.opt_out = True
        cls.blacklisted = added("black.bulk@example.com", cls.list_doi)
        cls.env["mail.blacklist"].sudo()._add("black.bulk@example.com")
        cls.no_email = Contact.create({"name": "No Email", "list_ids": [(6, 0, cls.list_doi.ids)]})
        visitor = cls.env(user=cls.public_user, su=True)

        def signed_up(email):
            contact = visitor["mailing.contact"].create({"name": "", "email": email})
            return visitor["mailing.subscription"].create(
                {"contact_id": contact.id, "list_id": cls.list_doi.id}
            )

        cls.pending = signed_up("pending.bulk@example.com")
        cls.confirmed = signed_up("confirmed.bulk@example.com")
        cls.confirmed._vmk_confirm()
        cls.contacts = (
            cls.ana
            | cls.ben
            | cls.unsubscribed
            | cls.blacklisted
            | cls.no_email
            | cls.pending.contact_id
            | cls.confirmed.contact_id
        )

    def _wizard(self, contacts, lists=None, user=None):
        """The wizard as the contacts list opens it, from a list's Recipients
        when `lists` is not given."""
        user = user or self.marketer
        context = {} if lists is not None else {"default_list_ids": self.list_doi.ids}
        action = contacts.with_user(user).with_context(**context).action_vmk_request_confirmation()
        form = Form(self.env[action["res_model"]].with_user(user).with_context(**action["context"]))
        if lists is not None:
            for mailing_list in lists:
                form.list_ids.add(mailing_list)
        return form

    def test_recipients_fill_in_the_list(self):
        form = self._wizard(self.contacts)
        self.assertEqual([ml.id for ml in form.list_ids], self.list_doi.ids)
        self.assertEqual(form.subscription_count, 2)
        self.assertIn(
            "2 confirmation emails will be sent. The contacts will not receive mailings from this "
            "list until they confirm.",
            form.summary,
        )

    def test_only_subscriptions_never_asked_are_sent(self):
        result = self._wizard(self.contacts).save().action_request_confirmation()
        self.assertEqual(result["params"]["message"], "2 confirmation requests sent.")

        asked = (self.ana | self.ben).subscription_ids.filtered(
            lambda sub: sub.list_id == self.list_doi
        )
        self.assertEqual(asked.mapped("vmk_confirmation_state"), ["pending", "pending"])
        for email in ("ana.bulk@example.com", "ben.bulk@example.com"):
            with self.subTest(email=email):
                self.assertEqual(len(self._mails(email)), 1)
                log = self._logs(email).filtered(lambda line: line.list_id == self.list_doi)
                self.assertEqual(log.mapped("action"), ["subscribed", "requested"])
                self.assertEqual(log[-1].source, "backend")
                self.assertEqual(log[-1].user_id, self.marketer)

        plain = self.ana.subscription_ids.filtered(lambda sub: sub.list_id == self.list_plain)
        self.assertFalse(plain.vmk_confirmation_state, "a list not chosen is left alone")
        self.assertFalse(self.unsubscribed.subscription_ids.vmk_confirmation_state)
        self.assertFalse(self.blacklisted.subscription_ids.vmk_confirmation_state)
        self.assertFalse(self.no_email.subscription_ids.vmk_confirmation_state)
        self.assertEqual(self.confirmed.vmk_confirmation_state, "confirmed")
        self.assertEqual(len(self._mails("pending.bulk@example.com")), 1, "no second link")
        for email in ("unsub.bulk@example.com", "black.bulk@example.com"):
            with self.subTest(email=email):
                self.assertFalse(self._mails(email))

    def test_lists_chosen_in_the_dialog(self):
        form = self._wizard(self.ana, lists=self.list_doi | self.list_plain)
        self.assertEqual(form.subscription_count, 2)
        self.assertIn(
            "2 confirmation emails will be sent. The contact will not receive mailings from these "
            "lists until they confirm.",
            form.summary,
        )
        result = form.save().action_request_confirmation()
        self.assertEqual(result["params"]["message"], "2 confirmation requests sent.")
        self.assertEqual(
            self.ana.subscription_ids.mapped("vmk_confirmation_state"), ["pending", "pending"]
        )

    def test_one_is_a_sentence_of_its_own(self):
        form = self._wizard(self.ben)
        self.assertIn("1 confirmation email will be sent.", form.summary)
        result = form.save().action_request_confirmation()
        self.assertEqual(result["params"]["message"], "1 confirmation request sent.")

    def test_the_language_chosen_for_contacts_without_one(self):
        self.env["res.lang"]._activate_lang("es_ES")
        partner = self.env["res.partner"].create({"name": "Ana", "lang": "en_US"})
        self.ana.partner_id = partner
        form = self._wizard(self.ana | self.ben)
        self.assertEqual(form.lang, self.marketer.lang, "the user's own by default")
        form.lang = "es_ES"
        form.save().action_request_confirmation()
        self.assertEqual(
            self.ben.subscription_ids.vmk_confirmation_lang, "es_ES", "no language known"
        )
        ana = self.ana.subscription_ids.filtered(lambda sub: sub.list_id == self.list_doi)
        self.assertEqual(ana.vmk_confirmation_lang, "en_US", "her contact's language wins")

    def test_nothing_to_send(self):
        form = self._wizard(self.confirmed.contact_id | self.pending.contact_id)
        self.assertEqual(form.subscription_count, 0)
        self.assertIn("None of these contacts", form.summary)
        with self.assertRaises(UserError):
            form.save().action_request_confirmation()

    def test_needs_email_marketing_rights(self):
        employee = new_test_user(self.env, login="vmk_doi_bulk_employee", groups="base.group_user")
        self.env.invalidate_all()
        with self.assertRaises(AccessError):
            self.env["vmk.mailing.request.confirmation"].with_user(employee).create(
                {"contact_ids": self.ben.ids, "list_ids": self.list_doi.ids}
            )
        self.assertFalse(self.ben.subscription_ids.vmk_confirmation_state)
