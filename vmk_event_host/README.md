# Event Hosts (`vmk_event_host`)

Adds **Hosts** to `event.event`: the people running the event, as contacts, in an order you set.

## Why core does not cover this

An event already names two parties, and neither is the person in the room:

- **Organizer** (`organizer_id`) is the company putting the event on, defaulting to the current
  company.
- **Responsible** (`user_id`) is the internal user who owns the record.

A teacher, speaker or facilitator is usually neither. They are frequently not an Odoo user at all,
which is why hosts are `res.partner` records rather than `res.users`.

## The model, and why it is a line model

`vmk.event.host` holds one row per host: `partner_id`, an optional `role` ("Lead", "Guest speaker"),
and `sequence`.

**Ordering is the whole reason it exists.** The first version of this module used a `Many2many`,
which cannot be ordered: the relation table has no column to hold a position, so records come back
in the target model's own order — `res.partner._order` is `complete_name ASC, id DESC`, i.e.
alphabetical. Hosts added as "Zoe, then Ada" came back as "Ada, Zoe", and nothing could reorder
them. A line model with a `sequence` gives drag-and-drop, and `role` came along for free.

Two fields on `event.event` exist because that line model costs what a many2many gave for nothing:

- **`vmk_host_partner_ids`** — a stored, computed `Many2many` mirror of the lines' contacts. Neither
  grouping nor an `in` domain works on a one2many, so the search view, the "Group by > Host" filter
  and the optional list column all read this. It carries `tracking=True`, so host changes reach the
  chatter as Responsible and Organizer changes do.
- **`vmk_host_names`** — a computed `Char` for the form header. The mirror could not be used there:
  being a many2many it renders alphabetically, so the header would contradict the order set in the
  Hosts tab.

**`vmk_host_names` sorts the lines itself** rather than trusting `vmk_host_ids` to come back in
order. A one2many keeps the order it was read in until the cache is invalidated, so writing
`sequence` — which is exactly what dragging a row does — leaves the recordset in its old order
within the same transaction. Without the explicit `sorted()`, the header lagged a drag by one save.
A test covers it.

## The summary opens the tab

Clicking the header summary switches the form to the Hosts tab, so the field behaves like any other
field that takes you where you can edit it.

`vmk_host_summary` is a small field widget doing that. **The notebook keeps its active page in
component state with no public way in** (`web/static/src/core/notebook/notebook.js`), so the widget
clicks the tab the user would have clicked. That tab is findable by name rather than by position or
label, because `Notebook`'s template renders `t-att-name` on each `.nav-link`; the page to open is a
field option (`options="{'page': 'vmk_hosts'}"`) rather than hard-coded.

It renders a real `<button>`, not a styled `<div>`: a div is invisible to the keyboard and to a
screen reader. Its accessible name says what the control does rather than only what it reads — "Ada
Lovelace, Zoe — show the Hosts tab" — with the visible text kept as a substring, per WCAG 2.5.3.

## Other decisions

**Prefixed field names.** `vmk_host_ids`, not `host_ids`. Field names on a core model are a shared
namespace: another module defining `host_ids` with a different type on `event.event` would break
installs that have both.

**A unique constraint on `(event_id, partner_id)`**, so the same contact cannot be listed twice on
one event. It is a SQL constraint, so it surfaces as `IntegrityError`, not `ValidationError`.

**Access rights mirror core's own event rules**: read for the registration desk, full rights for
event users and managers. The multi-company record rule mirrors
`event.ir_rule_event_event_ticket_company` — a host line is reachable exactly when its event is.

**Views are anchored on fields and named pages, never on the root tag.**
`<field name="user_id" position="after">` and `<page name="tickets" position="after">` survive core
renaming its own elements; the `<tree>` to `<list>` rename in Odoo 18 broke exactly that kind of
xpath.

## Licence: LGPL-3, not this repo's AGPL-3 default

Our own proprietary modules depend on this one: `vmk_event_sessions` (sessions under an event) is
OPL-1, and the glue module that puts a host on a session depends on both.

Odoo's licence-compatibility table (in its [Apps FAQ](https://apps.odoo.com/apps/faq)) permits an
OPL-1 or OEEL-1 module to depend on LGPL-3, but **not** on AGPL-3. AGPL here would therefore make
that glue impossible to license at all. This is the repo's stated exception — LGPL for a module
meant to be depended on — and the same reasoning behind `vmk_partner_email_multiple`.

## Testing

```bash
cd "../Tech Stack/odoo-dev"
./odev install vmk_event_host
./odev test vmk_event_host
```
