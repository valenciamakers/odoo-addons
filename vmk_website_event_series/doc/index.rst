One page on your website for an event you run again and again, always at the same address.

In standard Odoo, every date of a monthly workshop has a page of its own, which goes out of date
when the event is over. This module gives each series of `Event Series
<https://apps.odoo.com/apps/modules/20.0/vmk_event_series>`_ one page: what it is about, and its
current and upcoming dates, each linking to its own page to register.

**Installation**

Install **Event Series (Website)** from the Apps menu. It requires **Event Series**, which it
includes, and Odoo's **Events** app. Once both are installed, it installs itself.

**Using it**

#. Open a series in **Events › Series**, and switch on **Published**, as for an event. To publish it
   later, set **Publish on** instead. A series can also be limited to one website.
#. Click **Go to Website**. The page, at ``/event/series/<series>``, shows the series' cover, name,
   and subtitle, its description, and its current and upcoming dates.
#. Edit the cover, name, subtitle, and description on the page itself, in the website editor, as for
   an event. A new series starts with a sample description, as a new event does, saying that the
   event is repeated and that each date has its own tickets.

The dates are listed as on the events listing, ``/event``, so its layout options and your theme
apply to them too. With no dates scheduled, the page says so.

**Elsewhere on the website**

- **The events listing** has a **Series** filter beside its date filter, once a series is
  published.
- **An event's page** has a **Series** block in its sidebar, beside **Location** and **Organizer**,
  linking to its series once the series is published.
- **The index page**, ``/events/series``, lists every published series on the website, each with
  its next date.

**To serve the pages at another address**, such as ``/workshops``, add two redirects of type **308
Redirect / Rewrite** in **Website › Configuration › Redirects**, one for each page: from
``/events/series`` to ``/workshops``, and from ``/event/series/<model("vmk.event.series"):series>``
to ``/workshops/<model("vmk.event.series"):series>``. Odoo then serves the pages at the new
address, redirects the old one there, and changes the site's links to match.

**Limits**

- **Past dates are not listed** on a series' page, only the current and upcoming ones.
- **The events listing still shows every date** of a series, rather than the series once.
- **A visitor sees only published series and dates.** An unpublished series' page is not found, and
  its link on an event's page is not shown.

**Languages**

English, Spanish, and Catalan. If any translation seems incorrect, please
`contact us <mailto:info@valenciamakers.es>`_ and we will fix it.

**Changelog**

*20.0.1.0.0 (25 November 2026)*

- First release.
