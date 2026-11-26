Group events that are offered multiple times, such as a monthly workshop, into one series.

In standard Odoo, a workshop you run every month is a dozen unrelated events. This module groups
them into one series. Each date stays an ordinary event, with its own tickets, seats, and
registrations, and the series keeps them together.

**Installation**

Install **Event Series** from the Apps menu. It only requires **Events Organization**, the backend
part of the **Events** app.

If you publish events on your website, install `Event Series (Website)
<https://apps.odoo.com/apps/modules/20.0/vmk_website_event_series>`_ instead: it includes this
module, and also gives each series a page of its own on your website, listing its upcoming dates. If
you start publishing events online later, install Event Series (Website) then.

**Using it**

#. Open **Events › Series** and click **New**.
#. Give the series a name and, optionally, a subtitle and a **Template**. The template is what its
   new dates start from, as for any event.
#. Save, then click **New Event in Series**. It opens a new event already in the series, named after
   it and filled in from its template, ready for its date.

**An event's Series field**, beside **Template** on the event form, adds an existing event to a
series. Unlike the template, it fills nothing in: the event's tickets, communications, and
everything else stay as they were. Moving an event to another series works the same way.

**The Upcoming Events button** on a series opens its events, and counts the current and upcoming
dates: events that have not yet ended. The form also shows the series' **Next Event**.

**Events can be searched and grouped by series**, and the events list has a **Series** column.

**Who can do what.** Event users create and edit series, event managers can also delete them, and
the registration desk can read them.

**Limits**

- **A series doesn't create dates for you.** Each date is an event you create, with **New Event in
  Series** or as usual.
- **Each date is its own event.** A change that should reach every date, such as a new ticket
  price, is made on each one, as in standard Odoo.
- **A series with events can't be deleted**, only archived, so no event is left pointing at nothing.
  A series without events can be deleted.
- **On its own, this module doesn't change the website.** **Event Series (Website)** gives each
  series a page.

**Languages**

English, Spanish, and Catalan. If any translation seems incorrect, please
`contact us <mailto:info@valenciamakers.es>`_ and we will fix it.

**Changelog**

*20.0.1.0.0 (25 November 2026)*

- First release.
