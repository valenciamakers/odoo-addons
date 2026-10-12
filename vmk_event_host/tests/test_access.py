# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import Command
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestHostAccess(TransactionCase):
    """The module as users other than the superuser meet it.

    Every fixture is created by the superuser and sits in a cache shared across
    users, so a read as another user comes back without an access check unless
    the cache is invalidated first: each test does, before it acts as the user.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.env["res.company"].create({"name": "Company A"})
        cls.company_b = cls.env["res.company"].create({"name": "Company B"})

    def _user(self, login, company, *groups):
        return self.env["res.users"].create(
            {
                "name": login,
                "login": login,
                "company_id": company.id,
                "company_ids": [Command.set(company.ids)],
                "group_ids": [
                    Command.set(
                        [self.env.ref("base.group_user").id]
                        + [self.env.ref(group).id for group in groups]
                    )
                ],
            }
        )

    def _event(self, name, company, hosts=()):
        return self.env["event.event"].create(
            {
                "name": name,
                "company_id": company.id if company else False,
                "date_begin": "2026-10-05 16:00:00",
                "date_end": "2026-10-05 18:30:00",
                "vmk_host_ids": [Command.create({"partner_id": host.id}) for host in hosts],
            }
        )

    def test_a_partner_manager_outside_events_can_merge_hosts(self):
        """The wizard belongs to partner managers, who have no access to the
        host model: the merge used to raise an AccessError for them."""
        manager = self._user("vmk_host_merger", self.company_a, "base.group_partner_manager")
        ada, zoe = self.env["res.partner"].create([{"name": "Ada"}, {"name": "Zoe"}])
        event = self._event("Intro", self.company_a, hosts=(ada, zoe))
        self.env.invalidate_all()
        self.env["base.partner.merge.automatic.wizard"].with_user(manager)._merge(
            [ada.id, zoe.id], dst_partner=zoe
        )
        self.assertFalse(ada.exists())
        self.assertEqual(event.vmk_host_ids.partner_id, zoe)
        self.assertEqual(len(event.vmk_host_ids), 1)

    def test_a_merge_dedupes_hosts_of_an_event_of_another_company(self):
        """The company rule hides the other company's lines from an event user, so
        a dedupe run as the user left the survivor listed twice."""
        user_b = self._user(
            "vmk_host_merger_b",
            self.company_b,
            "event.group_event_user",
            "base.group_partner_manager",
        )
        ada, zoe = self.env["res.partner"].create([{"name": "Ada"}, {"name": "Zoe"}])
        event = self._event("Intro A", self.company_a, hosts=(ada, zoe))
        self.env.invalidate_all()
        self.env["base.partner.merge.automatic.wizard"].with_user(user_b)._merge(
            [ada.id, zoe.id], dst_partner=zoe
        )
        self.assertEqual(len(event.vmk_host_ids), 1)
        self.assertEqual(event.vmk_host_ids.partner_id, zoe)

    def test_the_form_opens_for_a_user_who_cannot_read_a_host_contact(self):
        """A many2one shows its display name whatever the target's own rules say;
        the line's name and the summary have to do the same."""
        user_b = self._user("vmk_host_viewer_b", self.company_b, "event.group_event_user")
        host = self.env["res.partner"].create(
            {"name": "Hidden Host", "company_id": self.company_a.id}
        )
        event = self._event("Shared", None, hosts=(host,))
        line = event.vmk_host_ids
        self.env.invalidate_all()
        self.assertFalse(host.with_user(user_b).has_access("read"))
        self.assertEqual(event.with_user(user_b).vmk_host_names, "Hidden Host")
        self.env.invalidate_all()
        self.assertEqual(line.with_user(user_b).display_name, "Hidden Host")
