# Event Series (Website) (`vmk_website_event_series`)

A page on the website for each event series of [`vmk_event_series`](../vmk_event_series), always at
the same address, describing the series and listing its current and upcoming dates; an index of
every series; a link from each event's page to its series; and a Series filter on the `/event`
listing.

It depends on `vmk_event_series` and `website_event`, and installs itself once both are there.
LGPL-3, © 2026 Valencia Makers, SL.

## How to use it

- **Publish a series** from its form, as an event is: the Published toggle, Publish on to schedule
  it (website's own cron publishes it then), and the Go to Website button. A series can be limited
  to one website.
- **Its page**, at `/event/series/<series>`, shows its cover, name, and subtitle, its description,
  and its current and upcoming events, in the same list as the `/event` listing's. The cover, name,
  subtitle, and description are edited on the page, in the website editor. A new series starts with
  a sample description, as a new event does, saying that the event is repeated and each date has its
  own tickets. The description, as an event's, is written only there: no form shows it. With no
  dates scheduled, the page says so.
- **`/events/series`** lists every published series on the website, each with its next event. The
  list is in the plural and each series in the singular, as `/events` lists events and
  `/event/<event>` is one.
- **An event's page** has a Series block in its sidebar, beside Location and Organizer, linking to
  its series, once the series is published.
- **The `/event` listing** has a Series filter beside its Date filter, once a series is published,
  drawn as its tag categories' filters are: titled Series, All first, and a count once one is
  chosen.
- **To serve the pages at another address**, such as `/workshops`, add two redirects of type "308
  Redirect / Rewrite" in Website › Configuration › Redirects, one for each route: from
  `/events/series` to `/workshops`, and from `/event/series/<model("vmk.event.series"):series>` to
  `/workshops/<model("vmk.event.series"):series>`. Odoo then serves the pages at the new address,
  redirects the old one there, and rewrites the site's links to them.

## For developers

### What the page is built from

The series takes website's own mixins, as `event.event` does in `website_event`:
`website.published.multi.mixin` (published, per website), `website.seo.metadata`, and
`website.cover_properties.mixin`. Its `website_url` is `/event/series/<slug>`, and link previews
take its cover and subtitle, as an event's do. Its events, under the heading Events, are the
listing's own list, `website_event.events_list`, wrapped as `website_event.index` wraps it
(`o_wevent_index`, `o_wevent_events_list`, `#o_wevent_index_main_col`), so the listing's styles, its
layout options (columns or rows, cards), and a theme's styling of the listing all apply. The list's
search and pager have nothing to do on this page, so they get an empty search and a pager of one
page, which draws nothing.

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
