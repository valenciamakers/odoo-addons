# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo.exceptions import AccessError
from odoo.orm.models import get_public_method
from odoo.tests import tagged
from odoo.tests.common import new_test_user

from .common import DoubleOptInCommon


@tagged("post_install", "-at_install")
class TestAccess(DoubleOptInCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee = new_test_user(cls.env, login="vmk_doi_employee", groups="base.group_user")
        cls.portal = new_test_user(cls.env, login="vmk_doi_portal", groups="base.group_portal")
        cls.admin = new_test_user(
            cls.env, login="vmk_doi_admin", groups="base.group_user,base.group_system"
        )
        cls.contact = cls.env["mailing.contact"].create(
            {"name": "Zed", "email": "zed@example.com", "list_ids": [(6, 0, cls.list_doi.ids)]}
        )
        cls.subscription = cls.contact.subscription_ids
        cls.log = cls.Log.search([("email", "=", "zed@example.com")])

    def setUp(self):
        super().setUp()
        # The cache is shared across users: without this, values read as the
        # superuser in setUpClass come back to any user with no access check.
        self.env.invalidate_all()

    def test_email_marketing_users_read_the_log_and_nothing_more(self):
        log = self.log.with_user(self.marketer)
        self.assertEqual(log.action, "subscribed")
        for operation in ("create", "write", "unlink"):
            with self.subTest(operation=operation):
                self.assertFalse(log.has_access(operation))

    def test_settings_administrators_may_delete_lines(self):
        log = self.log.with_user(self.admin)
        self.assertTrue(log.has_access("unlink"))
        self.assertFalse(log.has_access("write"))
        self.assertFalse(log.has_access("create"))
        log.unlink()
        self.assertFalse(self.log.exists())

    def test_nobody_else_reads_the_log(self):
        for user in (self.employee, self.portal, self.public_user):
            with self.subTest(user=user.login):
                with self.assertRaises(AccessError):
                    self.log.with_user(user).read(["email"])

    def test_requesting_confirmation_needs_write_access(self):
        for user in (self.employee, self.portal):
            with self.subTest(user=user.login):
                with self.assertRaises(AccessError):
                    self.subscription.with_user(user).action_vmk_request_confirmation()
        self.assertFalse(self.subscription.vmk_confirmation_state)
        self.assertFalse(self._mails("zed@example.com"))

    def test_only_the_action_is_callable_over_rpc(self):
        Subscription = self.env["mailing.subscription"]
        self.assertTrue(get_public_method(Subscription, "action_vmk_request_confirmation"))
        for name in ("_vmk_confirm", "_vmk_request_confirmation", "_vmk_confirmation_token"):
            with self.subTest(name=name), self.assertRaises(AccessError):
                get_public_method(Subscription, name)
        with self.assertRaises(AccessError):
            get_public_method(self.Log, "_vmk_log")

    def test_the_contact_form_counts_lines_for_its_readers(self):
        contact = self.contact.with_user(self.marketer)
        self.assertEqual(contact.vmk_consent_log_count, 1)
        action = contact.action_vmk_view_consent_log()
        self.assertEqual(self.Log.with_user(self.marketer).search(action["domain"]), self.log)
