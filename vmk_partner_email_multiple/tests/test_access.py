# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from lxml import etree

from odoo.exceptions import AccessError
from odoo.tests import new_test_user, tagged
from odoo.tools import file_open

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
        """Matching reads the table as superuser, and hands back the contact
        only where the user may see it: the same answer as before the rule."""
        resolved = self.PartnerEmail.with_user(self.user)._resolve_partners(
            ["alice.work@example.com"]
        )
        self.assertEqual(resolved["alice.work@example.com"], self.alice)

    def test_the_rule_is_cores_contact_rule(self):
        """Ours is a copy of `base.res_partner_rule`, reached through the
        contact. Core's is read from its file, not the database, where it is
        `noupdate` and may have been edited."""
        with file_open("base/security/base_security.xml", "rb") as source:
            core = etree.parse(source).xpath(
                "//record[@id='res_partner_rule']/field[@name='domain_force']"
            )[0].text
        ours = self.env.ref("vmk_partner_email_multiple.vmk_partner_email_company_rule")
        self.assertEqual(ours.domain_force.replace("partner_id.", ""), core)
