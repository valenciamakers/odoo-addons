# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from werkzeug.exceptions import NotFound

from odoo import http
from odoo.http import request

from odoo.addons.website_event.controllers.main import WebsiteEventController


def _published_series(env):
    website = env.website
    return env["vmk.event.series"].search(
        [("website_published", "=", True), *website.website_domain()]
    )


def sitemap_series(env, rule, qs):
    if not qs or qs.lower() in "/event/series":
        yield {"loc": "/event/series"}
    for series in _published_series(env):
        loc = series.website_url
        if not qs or qs.lower() in loc.lower():
            yield {"loc": loc}


class WebsiteEventSeriesController(WebsiteEventController):

    # The /event listing's Series filter

    def _get_events_search_options(self, slug_tags, **post):
        options = super()._get_events_search_options(slug_tags, **post)
        options["series"] = post.get("series")
        return options

    @http.route()
    def events(self, page=1, slug_tags=None, **searches):
        response = super().events(page=page, slug_tags=slug_tags, **searches)
        if getattr(response, "qcontext", None) is not None:
            series = _published_series(request.env)
            current = searches.get("series")
            response.qcontext.update({
                "vmk_series": series,
                "vmk_current_series": series.filtered(lambda s: str(s.id) == current),
            })
        return response

    # The series' own pages

    @http.route("/event/series", type="http", auth="public", website=True,
                sitemap=sitemap_series, readonly=True)
    def series_index(self, **kwargs):
        return request.render("vmk_website_event_series.series_index", {
            "series_list": _published_series(request.env),
        })

    @http.route('/event/series/<model("vmk.event.series"):series>', type="http",
                auth="public", website=True, sitemap=False, readonly=True)
    def series_page(self, series, **kwargs):
        # A series the visitor may not read, or one of another website, is
        # not there for them. Editors see an unpublished one, to publish it.
        if not series.has_access("read") or not series._is_on_current_website():
            raise NotFound()
        return request.render("vmk_website_event_series.series_page", {
            "series": series,
            "events": series._website_events(),
            "main_object": series,
        })
