# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

import ast

from odoo import Command
from odoo.exceptions import AccessError
from odoo.tests import new_test_user, tagged

from .common import PartnerEmailCase


@tagged("post_install", "-at_install")
class TestPartnerEmailAccess(PartnerEmailCase):
    """An additional address is as visible as the contact it belongs to."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = new_test_user(cls.env, login="vmk_email_user", groups="base.group_user")
        other_company = cls.env["res.company"].create({"name": "Another Company"})
        cls.hidden = cls.Partner.create(
            {
                "name": "Hidden Example",
                "email": "hidden@example.com",
                "company_id": other_company.id,
                "vmk_email_ids": [(0, 0, {"email": "hidden.work@example.com"})],
            }
        )

    def test_the_fixture_contact_is_hidden_by_core(self):
        """The premise: core keeps the contact itself from this user."""
        with self.assertRaises(AccessError):
            self.hidden.with_user(self.user).read(["email"])

    def test_an_address_is_hidden_with_its_contact(self):
        """A direct read of the model, which is what the rule is for."""
        rows = self.alice.vmk_email_ids + self.hidden.vmk_email_ids
        found = self.PartnerEmail.with_user(self.user).search([("id", "in", rows.ids)])
        self.assertEqual(found, self.alice.vmk_email_ids)
        with self.assertRaises(AccessError):
            self.hidden.vmk_email_ids.with_user(self.user).read(["email"])

    def test_matching_is_not_narrowed(self):
        """Matching reads the table as superuser, so the rule changes nothing
        for a contact the user may see."""
        resolved = self.PartnerEmail.with_user(self.user)._resolve_partners(
            ["alice.work@example.com"]
        )
        self.assertEqual(resolved["alice.work@example.com"], self.alice)

    def test_a_hidden_contact_is_not_resolved(self):
        """Core's search, under the user's rules, would not find it; neither
        may we. Handed back anyway, it broke `mail.thread`'s resolution step,
        which reads every partner returned, with an AccessError."""
        resolved = self.PartnerEmail.with_user(self.user)._resolve_partners(
            ["hidden.work@example.com"]
        )
        self.assertEqual(resolved, {})
        found = self.Partner.with_user(self.user)._find_or_create_from_emails(
            ["hidden.work@example.com"], no_create=True
        )
        self.assertFalse(found[0])
        found = self.env["mail.thread"].with_user(self.user)._mail_find_partner_from_emails(
            ["hidden.work@example.com"]
        )
        self.assertFalse(found[0])

    def test_a_hidden_primary_holder_does_not_block_a_visible_contact(self):
        """Who holds an address is answered per viewer, as core answers it.
        Between two primary holders core gives the user the one they can see;
        so a primary holder the user cannot see does not keep a visible
        contact's additional address from matching. The superuser, and so the
        mail gateway, still gets the primary holder."""
        hidden_primary = self.Partner.create(
            {
                "name": "Hidden Primary",
                "email": "shared@example.com",
                "company_id": self.hidden.company_id.id,
            }
        )
        self.PartnerEmail.create({"partner_id": self.alice.id, "email": "shared@example.com"})
        found = self.Partner.with_user(self.user)._find_or_create_from_emails(
            ["shared@example.com"], no_create=True
        )
        self.assertEqual(found[0], self.alice)
        found = self.Partner._find_or_create_from_emails(["shared@example.com"], no_create=True)
        self.assertEqual(found[0], hidden_primary)

    def test_users_without_access_to_the_table_can_still_search_contacts(self):
        """A dotted path on the one2many is a subquery under the caller's
        access, so widening display_name for a user with no ir.access
        permission on the table turned every contact search into an
        AccessError."""
        portal = new_test_user(self.env, login="vmk_email_portal", groups="base.group_portal")
        for user in (portal, self.env.ref("base.public_user")):
            with self.subTest(user=user.login):
                results = self.Partner.with_user(user).name_search("Alice")
                self.assertNotIn(
                    self.alice.id,
                    [result[0] for result in results],
                    "core's own rule keeps the contact from a portal or public user",
                )

    def test_the_restriction_defers_to_the_contacts_own_access(self):
        """The row states no company logic of its own: it asks for rows whose
        contact the user may read, through the `access` operator, so it follows
        core's contact restriction whatever that becomes. It keeps no group,
        which is what makes it a restriction on everyone and not a permission."""
        ours = self.env.ref("vmk_partner_email_multiple.vmk_partner_email_company_rule")
        self.assertEqual(ast.literal_eval(ours.domain), [("partner_id", "access", "read")])
        self.assertEqual(ours.operation, "crud")
        self.assertFalse(ours.group_id)

    def _company_user(self, login, company):
        return new_test_user(
            self.env,
            login=login,
            groups="base.group_user",
            company_id=company.id,
            company_ids=[Command.set(company.ids)],
        )

    def test_a_user_of_company_b_cannot_read_rows_of_a_share_contact_of_company_a(self):
        company_a, company_b = self.env["res.company"].create(
            [{"name": "Company A"}, {"name": "Company B"}]
        )
        user_b = self._company_user("vmk_email_user_b", company_b)
        contact = self.Partner.create({"name": "Share A", "company_id": company_a.id})
        row = self.PartnerEmail.create({"partner_id": contact.id, "email": "share.a@example.com"})
        self.assertTrue(contact.partner_share, "the premise: a plain contact is a share one")
        self.env.invalidate_all()
        self.assertFalse(contact.with_user(user_b).has_access("read"))
        self.assertFalse(row.with_user(user_b).has_access("read"))
        self.assertFalse(self.PartnerEmail.with_user(user_b).search([("id", "=", row.id)]))
        with self.assertRaises(AccessError):
            row.with_user(user_b).read(["email"])

    def test_a_user_can_read_rows_of_a_contact_with_no_company(self):
        company_b = self.env["res.company"].create({"name": "Company B"})
        user_b = self._company_user("vmk_email_user_b2", company_b)
        contact = self.Partner.create({"name": "Nobody's", "company_id": False})
        row = self.PartnerEmail.create({"partner_id": contact.id, "email": "nobody@example.com"})
        self.env.invalidate_all()
        self.assertTrue(contact.with_user(user_b).has_access("read"))
        self.assertEqual(self.PartnerEmail.with_user(user_b).search([("id", "=", row.id)]), row)
        self.assertEqual(row.with_user(user_b).email, "nobody@example.com")

    def test_the_rows_of_a_contact_follow_its_visibility(self):
        """Not a snapshot of core's rule: when the contact becomes readable, so
        do its rows, and the other way round. An internal user's own contact
        is readable by every company, as in core."""
        company_a, company_b = self.env["res.company"].create(
            [{"name": "Company A"}, {"name": "Company B"}]
        )
        user_a = self._company_user("vmk_email_user_a3", company_a)
        user_b = self._company_user("vmk_email_user_b3", company_b)
        contact = self.Partner.create({"name": "Moves", "company_id": company_a.id})
        row = self.PartnerEmail.create({"partner_id": contact.id, "email": "moves@example.com"})
        user_a_row = self.PartnerEmail.create(
            {"partner_id": user_a.partner_id.id, "email": "user.a@example.com"}
        )
        self.assertFalse(user_a.partner_id.partner_share)
        for expected, record_rows in (
            (False, row),
            (True, user_a_row),
        ):
            self.env.invalidate_all()
            found = self.PartnerEmail.with_user(user_b).search([("id", "in", record_rows.ids)])
            self.assertEqual(bool(found), expected, record_rows.email)
        contact.company_id = company_b
        self.env.invalidate_all()
        self.assertEqual(self.PartnerEmail.with_user(user_b).search([("id", "=", row.id)]), row)
        contact.company_id = company_a
        self.env.invalidate_all()
        self.assertFalse(self.PartnerEmail.with_user(user_b).search([("id", "=", row.id)]))
