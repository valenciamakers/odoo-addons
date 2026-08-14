# Copyright 2026 Valencia Makers, SL
# License MIT (https://opensource.org/licenses/MIT).

from lxml import etree

from odoo.tests import tagged
from odoo.tools.safe_eval import safe_eval

from .common import PartnerEmailCase


@tagged("post_install", "-at_install")
class TestPartnerEmailMatching(PartnerEmailCase):
    # ------------------------------------------------------------
    # _find_or_create_from_emails
    # ------------------------------------------------------------

    def test_additional_address_matches_instead_of_creating(self):
        before = self.Partner.search_count([])
        found = self.Partner._find_or_create_from_emails(["alice.work@example.com"])
        self.assertEqual(found, [self.alice])
        self.assertEqual(self.Partner.search_count([]), before, "no duplicate was created")

    def test_display_name_form_matches(self):
        found = self.Partner._find_or_create_from_emails(['"Alice" <Alice.Work@Example.com>'])
        self.assertEqual(found, [self.alice])

    def test_results_keep_input_order_when_spliced(self):
        """The wrapper hands only unresolved addresses to super(), so order matters."""
        found = self.Partner._find_or_create_from_emails(
            [
                "alice.work@example.com",  # additional -> alice
                "stranger@example.com",  # unknown    -> created
                "alice@example.com",  # primary    -> alice
                "noreply@alice-shop.example.com",  # additional -> alice
            ]
        )
        self.assertEqual(len(found), 4)
        self.assertEqual(found[0], self.alice)
        self.assertEqual(found[1].email, "stranger@example.com")
        self.assertNotEqual(found[1], self.alice)
        self.assertEqual(found[2], self.alice)
        self.assertEqual(found[3], self.alice)

    def test_no_create_still_matches_additional_addresses(self):
        before = self.Partner.search_count([])
        found = self.Partner._find_or_create_from_emails(
            ["alice.work@example.com", "stranger@example.com"], no_create=True
        )
        self.assertEqual(found[0], self.alice)
        self.assertFalse(found[1])
        self.assertEqual(self.Partner.search_count([]), before)

    def test_a_primary_holder_wins_over_an_additional_one(self):
        """Installing this module must never re-route mail core already matched."""
        carol = self.Partner.create({"name": "Carol Example", "email": "shared@example.com"})
        self.PartnerEmail.create({"partner_id": self.alice.id, "email": "shared@example.com"})
        found = self.Partner._find_or_create_from_emails(["shared@example.com"])
        self.assertEqual(found, [carol])

    def test_banned_addresses_are_not_resolved(self):
        found = self.Partner._find_or_create_from_emails(
            ["alice.work@example.com"],
            ban_emails=["alice.work@example.com"],
            no_create=True,
        )
        self.assertFalse(found[0], "a banned address must not reach a contact by the side door")

    def test_filter_found_is_honoured(self):
        found = self.Partner._find_or_create_from_emails(
            ["alice.work@example.com"], filter_found=lambda p: p.user_ids, no_create=True
        )
        self.assertFalse(found[0], "alice has no user, so the filter should reject her")

    def test_archived_contacts_are_skipped(self):
        """Core's own search would not find an archived contact either."""
        self.alice.active = False
        found = self.Partner._find_or_create_from_emails(
            ["alice.work@example.com"], no_create=True
        )
        self.assertFalse(found[0])

    # ------------------------------------------------------------
    # The other two entry points
    # ------------------------------------------------------------

    def test_legacy_find_or_create(self):
        before = self.Partner.search_count([])
        self.assertEqual(self.Partner.find_or_create("alice.work@example.com"), self.alice)
        self.assertEqual(self.Partner.search_count([]), before)

    def test_mail_find_partner_from_emails(self):
        """Core finds the right contact here and then drops it on the way out."""
        found = self.env["mail.thread"]._mail_find_partner_from_emails(
            ["alice.work@example.com"]
        )
        self.assertEqual(found, [self.alice])

    def test_mail_find_partner_from_emails_keeps_order(self):
        found = self.env["mail.thread"]._mail_find_partner_from_emails(
            ["alice@example.com", "nobody@example.com", "alice.work@example.com"]
        )
        self.assertEqual(found[0], self.alice)
        self.assertFalse(found[1])
        self.assertEqual(found[2], self.alice)

    # ------------------------------------------------------------
    # Search
    # ------------------------------------------------------------

    def test_autocomplete_finds_additional_addresses(self):
        results = self.Partner.name_search("noreply@alice-shop")
        self.assertIn(self.alice.id, [result[0] for result in results])

    def test_autocomplete_still_finds_the_usual_things(self):
        results = self.Partner.name_search("Alice Example")
        self.assertIn(self.alice.id, [result[0] for result in results])

    def _search_view_domain(self, field_name, term):
        """Run a search view entry the way the interface does.

        Reads the combined arch rather than our own snippet, so the assertion
        covers the inheritance actually landing on core's view.
        """
        view = self.Partner.get_view(
            self.env.ref("base.view_res_partner_filter").id, "search"
        )
        node = etree.fromstring(view["arch"]).xpath(f"//field[@name='{field_name}']")[0]
        return safe_eval(node.get("filter_domain"), {"self": term})

    def test_searching_by_email_finds_additional_addresses(self):
        domain = self._search_view_domain("email", "noreply@alice-shop")
        self.assertIn(self.alice, self.Partner.search(domain))

    def test_searching_by_email_still_finds_the_primary(self):
        domain = self._search_view_domain("email", "alice@example.com")
        self.assertIn(self.alice, self.Partner.search(domain))

    def test_searching_by_email_excludes_non_matches(self):
        bob = self.Partner.create({"name": "Bob Example", "email": "bob@example.com"})
        domain = self._search_view_domain("email", "alice")
        self.assertNotIn(bob, self.Partner.search(domain))

    def test_searching_by_name_covers_additional_addresses(self):
        """Core routes this one through display_name, which is already widened."""
        domain = self._search_view_domain("name", "noreply@alice-shop")
        self.assertIn(self.alice, self.Partner.search(domain))
