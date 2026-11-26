# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo.tests.common import TransactionCase, new_test_user


class DoubleOptInCommon(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.public_user = cls.env.ref("base.public_user")
        cls.marketer = new_test_user(
            cls.env,
            login="vmk_doi_marketer",
            groups="base.group_user,mass_mailing.group_mass_mailing_user",
        )
        cls.list_doi = cls.env["mailing.list"].create({"name": "VMK Newsletter", "is_public": True})
        cls.list_plain = cls.env["mailing.list"].create(
            {"name": "VMK Plain List", "is_public": True, "vmk_double_optin": False}
        )
        cls.Log = cls.env["vmk.mailing.consent.log"]

    def _visitor_env(self, **context):
        """The environment core's website controllers subscribe visitors in:
        the public user's, under `sudo()`, which keeps the uid."""
        return self.env(user=self.public_user, su=True, context=dict(self.env.context, **context))

    def _subscribe_as_visitor(self, email, mailing_list, **context):
        """What core's newsletter block does for an unknown address."""
        env = self._visitor_env(**context)
        contact = env["mailing.contact"].create({"name": "", "email": email})
        return env["mailing.subscription"].create(
            {"contact_id": contact.id, "list_id": mailing_list.id}
        )

    def _logs(self, email):
        return self.Log.search([("email", "=", email)], order="id")

    def _mails(self, email):
        return self.env["mail.mail"].sudo().search([("email_to", "=", email)], order="id")
