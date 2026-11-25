# Event Series (Website) (`vmk_website_event_series`)

A page on the website for each event series of [`vmk_event_series`](../vmk_event_series), always at
the same address, describing the series and listing its current and upcoming dates; an index of
every series; a link from each event's page to its series; and a Series filter on the `/event`
listing.

**How to use it** is in the user documentation, [`doc/index.rst`](doc/index.rst), which the Odoo
Apps Store also shows on the module's page, together with the changelog.

It depends on `vmk_event_series` and `website_event`, and installs itself once both are there.
LGPL-3, © 2026 Valencia Makers, SL.

## For developers

### What the page is built from

The index is `/events/series` and each series `/event/series/<slug>`: the list in the plural and
each series in the singular, as `/events` lists events and `/event/<event>` is one. A series'
description, as an event's, is written only on its page: no form shows it.

The series takes website's own mixins, as `event.event` does in `website_event`:
`website.published.multi.mixin` (published, per website), `website.seo.metadata`, and
`website.cover_properties.mixin`. Its `website_url` is `/event/series/<slug>`, and link previews
take its cover and subtitle, as an event's do. Its events, under the heading Events, are the
listing's own list, `website_event.events_list`, wrapped as `website_event.index` wraps it
(`o_wevent_index`, `o_wevent_events_list`, `#o_wevent_index_main_col`), so the listing's styles, its
layout options (columns or rows, cards), and a theme's styling of the listing all apply. The list's
search and pager have nothing to do on this page, so they get an empty search and a pager of one
page, which draws nothing.

**The cover lays its title over its image as an event's does.** `website.record_cover` positions the
image and its darkening filter absolutely, which paints them over the title and subtitle, as these
are not positioned. website_event gives its event cover a stacking context and puts those layers
behind it (`event_templates_page.scss`, `.o_wevent_event .o_record_cover_container`);
`static/src/scss/series_page.scss` does the same for ours. Without it, a series with a cover image
showed no title at all, found taking the store screenshots on 25 November 2026.

`_website_events()` is the series' events that have not ended, on the current website and visible to
the visitor, soonest first: published ones to a visitor, and unpublished ones too to whoever may see
those, as on `/event`.

### Who sees what

A visitor reads published series only (`security/ir.access.csv`, the public and portal row), and an
internal user every series, as `website_event` pairs its own rows for events. A series the visitor
may not read, or one limited to another website, is a 404. The event page's link reads the series as
superuser, so a visitor never meets an access error there, and shows only a published series on the
current website.

### The listing's filter

The `/event` listing builds its search from `_get_events_search_options` and
`event.event._search_get_detail`. The controller adds a `series` option, and the model adds its
domain to the list's and to the counts' domains, as website_event's own filters do. Its
`keep_event_url` carries any filter that is not `all`, so the series stays chosen across the other
filters and the pager. The dropdown and the small screens' filter panel are inherited from
`website_event.index_topbar`, beside the Date filter.

### Not yet

Past dates are not listed on the page, and the `/event` listing still shows every date rather than
each series once; both left for later on purpose.

### Translations

The module's own name and summary are guarded by `tests/test_translations.py`, as in every module
here. The fields website's mixins bring are taken in core's wording; where core's Catalan has none,
ours follows core's for the field beside it.

### Testing

`tests/test_website.py` checks the page's dates (current and upcoming, published, in order), the
page without dates, a new series' sample description, a 404 for an unpublished series, the index,
the event page's link, the listing's filter, and the sitemap. `tests/test_tours.py` filters the
listing by series in a browser, opens the event, and follows its link to the series' page.
