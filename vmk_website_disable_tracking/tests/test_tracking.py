# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from lxml import html

from odoo.addons.http_routing.tests.common import MockRequest
from odoo.tests.common import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestVisitorTracking(HttpCase):
    """A website with tracking off records no visitor, however it is asked."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # The first website exists before this module does, so what it holds
        # is what installing the module left it with.
        cls.website = cls.env["website"].browse(1)
        # A page made as the editor makes one, which website marks tracked.
        cls.page = cls.env["website.page"].browse(
            cls.website.with_context(website_id=cls.website.id).new_page("Tracked page", add_menu=False)["page_id"]
        )
        cls.page.is_published = True
        cls.env["website.visitor"].search([]).unlink()

    def _visitors(self):
        return self.env["website.visitor"].sudo().search_count([])

    def _tracking_mark(self):
        response = self.url_open(self.page.url)
        self.assertEqual(response.status_code, 200)
        return html.fromstring(response.content).get("data-tracking-enabled")

    def _report_a_view(self):
        """What the page's tracker sends three seconds after a page loads."""
        self.make_jsonrpc_request("/website/odoo_track", {"res_model": "website.page", "res_id": self.page.id})

    def _forced_visitor(self):
        """What a form gets when it links its record to the visitor.

        A CRM lead or an event registration asks for one with force_create,
        which makes it if there is none.
        """
        with MockRequest(self.env, website=self.website):
            return self.env["ir.http"]._get_visitor_from_request(force_create=True)

    def test_off_after_install(self):
        # Installing the module leaves tracking off on the website that was
        # already there, and on one made afterwards.
        self.assertFalse(self.website.vmk_track_visitors)
        self.assertFalse(self.env["website"].create({"name": "Another website"}).vmk_track_visitors)

    def test_off_records_nothing(self):
        self.assertTrue(self.page.track)
        # The page no longer asks the browser to report the view.
        self.assertFalse(self._tracking_mark())
        # Nor is a view reported by hand recorded.
        self._report_a_view()
        self.assertEqual(self._visitors(), 0)

    def test_on_records_visitors(self):
        # Ticking Track Visitors gives back Odoo's own behaviour.
        self.website.vmk_track_visitors = True
        self.assertTrue(self._tracking_mark())
        self._report_a_view()
        self.assertEqual(self._visitors(), 1)

    def test_forms_get_none_when_off(self):
        visitor = self._forced_visitor()
        # Empty, as website returns when it finds none, which callers handle.
        self.assertEqual(visitor._name, "website.visitor")
        self.assertFalse(visitor)
        self.assertEqual(self._visitors(), 0)

    def test_forms_get_a_visitor_when_on(self):
        self.website.vmk_track_visitors = True
        self.assertTrue(self._forced_visitor())
        self.assertEqual(self._visitors(), 1)
