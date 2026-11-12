# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from datetime import timedelta

from lxml import html

from odoo import fields
from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestSeriesWebsite(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        now = fields.Datetime.now()
        Series = cls.env["vmk.event.series"]
        cls.series = Series.create({
            "name": "Intro to 3D Printing",
            "subtitle": "One evening, one print",
            "is_published": True,
        })
        cls.hidden = Series.create({"name": "Secret Series"})

        def event(name, days, series, published=True):
            return {
                "name": name,
                "series_id": series.id,
                "date_begin": now + timedelta(days=days),
                "date_end": now + timedelta(days=days, hours=2),
                "is_published": published,
            }

        cls.past, cls.soon, cls.later, cls.draft, cls.secret = cls.env["event.event"].create([
            event("VMK Past Date", -30, cls.series),
            event("VMK Next Date", 3, cls.series),
            event("VMK Later Date", 33, cls.series),
            event("VMK Draft Date", 10, cls.series, published=False),
            event("VMK Secret Date", 5, cls.hidden),
        ])
        cls.other = cls.env["event.event"].create({
            "name": "VMK Unrelated Event",
            "date_begin": now + timedelta(days=4),
            "date_end": now + timedelta(days=4, hours=2),
            "is_published": True,
        })

    def _get(self, url, status=200):
        response = self.url_open(url)
        self.assertEqual(response.status_code, status, url)
        return html.fromstring(response.content) if status == 200 else None

    def test_url(self):
        self.assertEqual(
            self.series.website_url,
            f"/event/series/{self.env['ir.http']._slug(self.series)}",
        )

    def test_series_page_lists_current_and_upcoming_dates(self):
        page = self._get(self.series.website_url)
        self.assertIn("Intro to 3D Printing", page.text_content())
        self.assertIn("One evening, one print", page.text_content())
        dates = page.xpath("//section[contains(@class, 'o_vmk_event_series_dates')]")[0].text_content()
        self.assertIn("VMK Next Date", dates)
        self.assertIn("VMK Later Date", dates)
        self.assertNotIn("VMK Past Date", dates)
        # A visitor sees only published dates.
        self.assertNotIn("VMK Draft Date", dates)
        self.assertLess(dates.index("VMK Next Date"), dates.index("VMK Later Date"))

    def test_series_page_uses_the_listings_list(self):
        """The events are website_event's own list, set out as /event sets it
        out, so its styles and layout options reach them."""
        page = self._get(self.series.website_url)
        section = page.xpath("//section[contains(@class, 'o_vmk_event_series_dates')]")[0]
        self.assertEqual(" ".join(section.xpath(".//h2")[0].text_content().split()), "Events")
        cards = section.xpath(
            ".//div[contains(@class, 'o_wevent_events_list')]//div[@id='o_wevent_index_main_col']"
            "//a[contains(@href, '/event/')]"
        )
        self.assertEqual(len(cards), 2)

    def test_new_series_starts_with_sample_description(self):
        """As a new event does: one text block, without template branding."""
        series = self.env["vmk.event.series"].create({"name": "Fresh Series"})
        block = html.fromstring(str(series.description))
        self.assertEqual(block.xpath("//section/@class"), ["s_text_block"])
        self.assertEqual(block.xpath("//h5")[0].text_content(), "One event, many dates")
        self.assertNotIn("data-oe-", str(series.description))

    def test_series_page_without_dates(self):
        empty = self.env["vmk.event.series"].create({"name": "Nothing Yet", "is_published": True})
        page = self._get(empty.website_url)
        self.assertTrue(page.xpath("//*[contains(@class, 'o_vmk_event_series_no_dates')]"))

    def test_an_unpublished_series_is_not_there_for_visitors(self):
        self._get(self.hidden.website_url, status=404)
        self.authenticate("admin", "admin")
        self._get(self.hidden.website_url)

    def test_index_lists_published_series(self):
        page = self._get("/events/series")
        text = page.text_content()
        self.assertIn("Intro to 3D Printing", text)
        self.assertNotIn("Secret Series", text)
        links = page.xpath("//a[contains(@class, 'o_vmk_event_series_card')]/@href")
        self.assertIn(self.series.website_url, links)
        card = page.xpath("//a[contains(@class, 'o_vmk_event_series_card')]")[0]
        self.assertIn("Next event:", card.text_content())

    def test_event_page_links_to_its_series(self):
        page = self._get(self.soon.website_url)
        links = page.xpath("//*[contains(@class, 'o_vmk_event_series_link')]//a/@href")
        self.assertEqual(links, [self.series.website_url])

    def test_event_page_of_an_unpublished_series_has_no_link(self):
        self.secret.is_published = True
        page = self._get(self.secret.website_url)
        self.assertFalse(page.xpath("//*[contains(@class, 'o_vmk_event_series_link')]"))

    def test_listing_filters_by_series(self):
        page = self._get(f"/event?series={self.series.id}&country=all")
        text = page.xpath("//div[contains(@class, 'o_wevent_events_list')]")[0].text_content()
        self.assertIn("VMK Next Date", text)
        self.assertNotIn("VMK Unrelated Event", text)
        # Titled Series, with a count, as a tag category's filter is; the
        # chosen series is the active entry.
        filter_ = page.xpath("//div[contains(@class, 'o_vmk_event_series_filter')]")[0]
        button = filter_.xpath(".//button")[0]
        self.assertEqual(" ".join(button.text_content().split()), "Series 1")
        active = filter_.xpath(".//a[contains(@class, 'active')]")
        self.assertEqual([" ".join(a.text_content().split()) for a in active], ["Intro to 3D Printing"])

    def test_listing_unfiltered(self):
        page = self._get("/event?country=all")
        text = page.xpath("//div[contains(@class, 'o_wevent_events_list')]")[0].text_content()
        self.assertIn("VMK Next Date", text)
        self.assertIn("VMK Unrelated Event", text)
        filter_ = page.xpath("//div[contains(@class, 'o_vmk_event_series_filter')]")[0]
        self.assertEqual(" ".join(filter_.xpath(".//button")[0].text_content().split()), "Series")
        options = [" ".join(a.text_content().split()) for a in filter_.xpath(".//a")]
        self.assertEqual(options[0], "All")
        self.assertIn("Intro to 3D Printing", options)
        active = filter_.xpath(".//a[contains(@class, 'active')]")
        self.assertEqual([" ".join(a.text_content().split()) for a in active], ["All"])
        self.assertNotIn("Secret Series", page.text_content())

    def test_publish_on_schedules_publishing(self):
        """Website's own cron publishes a series whose Publish on has come,
        as it does an event."""
        self.hidden.publish_on = fields.Datetime.now() - timedelta(minutes=1)
        self.env.ref("website.ir_cron_publish_scheduled_pages").method_direct_trigger()
        self.assertTrue(self.hidden.is_published)
        self.assertFalse(self.hidden.publish_on)

    def test_sitemap(self):
        response = self.url_open("/sitemap.xml")
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.series.website_url.encode(), response.content)
        self.assertNotIn(self.hidden.website_url.encode(), response.content)
