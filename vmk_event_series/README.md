# Event Series (`vmk_event_series`)

Group the dates of an event you run again and again, such as a monthly workshop, into one series.
Each date stays an ordinary event, with its own tickets, seats, and registrations; the series holds
what they share, and lists them.

**How to use it** is in the user documentation, [`doc/index.rst`](doc/index.rst), which the Odoo
Apps Store also shows on the module's page, together with the changelog.

It depends only on `event` (_Events Organization_). **On Odoo 18 a series has no page on the
website:** its website companion, `vmk_website_event_series`, is not ported to this series, because
it relies on scheduled publishing (`publish_on`), which Odoo's website mixins only gained in 20.
LGPL-3, © 2026 Valencia Makers, SL.

## For developers

What follows is how the module works and why it is built this way.

### Why a model of its own, not the template

Core's event template (`event.type`) looks like the place for this, but it is not a link. Choosing a
template on an event fills in about nine stored fields from it — tickets, communications, tags,
seats, questions, the note — so putting an existing event in a template-as-series, or correcting the
wrong one, would replace that event's tickets and communications. Templates also group differently:
one "Evening workshop" template can serve several series. And a public module that gave every
template a page would surprise anyone already using templates for "Conference" or "Webinar". So a
series is `vmk.event.series`, and `event.event.series_id` is a plain many2one that triggers nothing.
A series names a template only to start new dates from it.

### Deleting

`series_id` is `ondelete="restrict"`, so the database refuses to delete a series with events. An
`@api.ondelete` check refuses first, with a message saying to archive the series instead, since the
database's own refusal names only the constraint. Archived events count: they still point at the
series.

### Translations

The module's own name and summary are `ir.module.module` records whose xmlid belongs to `base`
(`base.module_vmk_event_series`), so Odoo 18's exporter (`--i18n-export`) attributes them to `base`
and leaves them out of our POT. They are kept in the POT and both PO files by hand, which
`tests/test_translations.py` guards: it fails if the POT loses either entry. Terms core already
translates are taken in core's wording. "Series" is both the menu and the event's field, one
catalogue entry, so one translation: the plural, "Series" and "Sèries", which reads right in the
menu, the filters, and the group-by, and passes on the event form. The model and the action are
"Event Series", as core names its own "Event Templates".

### Testing

`tests/test_series.py` checks the counts and the next event, a running event counting as current,
the series filling nothing in, New Event in Series and the template's defaults reaching the new
event, the events action, deleting with and without events, and access for each events group and
across companies. `tests/test_tours.py` drives New Event in Series from a series' form.
