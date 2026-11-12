# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

import json

from odoo import fields, models
from odoo.tools.translate import html_translate


class VmkEventSeries(models.Model):
    """A series' page on the website: published per website, with SEO
    settings and a cover, the building blocks Odoo's own event page uses."""

    _name = "vmk.event.series"
    _inherit = [
        "vmk.event.series",
        "website.seo.metadata",
        "website.published.multi.mixin",
        "website.cover_properties.mixin",
    ]

    def _default_description(self):
        # As event.event's: rendering_bundle=True keeps the template's
        # branding out of the stored HTML.
        return self.env["ir.ui.view"].with_context(rendering_bundle=True)._render_template(
            "vmk_website_event_series.series_default_description"
        )

    # Written on the series' page in the website editor, as an event's is:
    # neither form shows it. A new series starts with a sample block, as a
    # new event does.
    description = fields.Html(
        translate=html_translate,
        sanitize_attributes=False,
        sanitize_form=False,
        default=_default_description,
    )

    def _compute_website_url(self):
        super()._compute_website_url()
        for series in self:
            # No slug for a record not yet saved, as in an onchange.
            if series.id:
                series.website_url = "/event/series/%s" % self.env["ir.http"]._slug(series)

    def _website_events(self):
        """The series' current and upcoming events on the current website,
        as the visitor may see them: published ones, or unpublished ones to
        whoever may see those. Events not yet ended, soonest first."""
        self.ensure_one()
        website = self.env.website
        return self.env["event.event"].search([
            ("series_id", "=", self.id),
            ("date_end", ">=", fields.Datetime.now()),
            ("is_visible_on_website", "=", True),
            *website.website_domain(),
        ], order="date_begin, id")

    def _is_on_current_website(self):
        """On this website: for every website, or for this one."""
        self.ensure_one()
        return not self.website_id or self.website_id == self.env.website

    def _default_website_meta(self):
        """The cover and subtitle in link previews, as an event's page has
        them (website_event/models/event_event.py)."""
        res = super()._default_website_meta()
        cover = json.loads(self.cover_properties or "{}").get("background-image", "none")
        # background-image may quote its URL: url('/my/url')
        res["default_opengraph"]["og:image"] = cover[4:-1].strip("\"'")
        res["default_opengraph"]["og:title"] = self.name
        res["default_opengraph"]["og:description"] = self.subtitle
        res["default_twitter"]["twitter:card"] = "summary"
        res["default_meta_description"] = self.subtitle
        return res

    def get_backend_menu_id(self):
        return self.env.ref("event.event_main_menu").id
