# Event Hosts (`vmk_event_host`)

Adds a **Hosts** field to `event.event`: the people running the event, as contacts. Nothing else.

## Why core does not cover this

An event already names two parties, and neither is the person in the room:

- **Organizer** (`organizer_id`) is the company putting the event on, defaulting to the current
  company.
- **Responsible** (`user_id`) is the internal user who owns the record.

A teacher, speaker or facilitator is usually neither. They are frequently not an Odoo user at all,
which is why hosts are `res.partner` records rather than `res.users`.

## Design decisions

**Several hosts, not one.** `vmk_host_ids` is a `Many2many`. Workshops and courses are often
co-taught, and widening a `Many2one` later would be a breaking change needing a migration. The cost
is that "the host" is never a single value, so anything reading it handles a set.

**Prefixed field name.** `vmk_host_ids`, not `host_ids`. Field names on a core model are a shared
namespace: another module defining `host_ids` with a different type on `event.event` would break
installs that have both.

**Tracked.** `tracking=True`, matching `organizer_id` and `user_id`. Odoo 19 records many2many
changes in the chatter as a comma-separated before-and-after (`mail/models/mail_tracking_value.py`,
the `one2many, many2many, tags` branch).

**No access-rights file.** Adding a field to an existing model inherits that model's rules; an
`ir.model.access.csv` here would be dead weight.

**Views are anchored on fields, never on the root tag.** `<field name="user_id" position="after">`
survives core renaming its own elements — the `<tree>` to `<list>` rename in Odoo 18 broke exactly
that kind of xpath.

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
