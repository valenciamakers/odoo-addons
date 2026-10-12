# Event Hosts (`vmk_event_host`)

Record who runs an event, as one or more contacts: the instructors, speakers, and facilitators
people meet in the room. Each host has an optional role, hosts keep the order you set, and events
can be searched, grouped, and tracked by host.

**How to use it** is in the user documentation, [`doc/index.rst`](doc/index.rst), which the Odoo
Apps Store also shows on the module's page, together with the changelog.

It depends only on `event` (_Events Organization_). LGPL-3, © 2026 Valencia Makers, SL.

## For developers

Adds **Hosts** to `event.event`: the people running the event, as contacts, in an order you set.

### Why core does not cover this

An event already names two parties, and neither is the person in the room:

- **Organizer** (`organizer_id`) is the company putting the event on, defaulting to the current
  company.
- **Responsible** (`user_id`) is the internal user who owns the record.

A teacher, speaker or facilitator is usually neither. They are frequently not an Odoo user at all,
which is why hosts are `res.partner` records rather than `res.users`.

### The model, and why it is a line model

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

### The summary opens the tab

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

**The field's label opens the tab too, and that costs no code.** The button carries `props.id`, and
`web.FormLabel` renders `for="props.id"`; a `<button>` is a labelable element, so the browser
forwards the label's click to it.

**It is styled as plain text on purpose.** Odoo shows no hyperlinks in this part of a form, so a
blue underlined value would read as a different kind of thing. The button keeps the field's own
colour and no underline, and `host_summary_field.scss` puts the ordinary cursor back: Bootstrap's
reboot sets `cursor: pointer` on every enabled button via `button:not(:disabled)`, so the override
has to out-specify that rule rather than merely follow it.

### The Hosts list is left alone on purpose

It behaves like any editable list: the cell shows a pointer, a click puts the row in edit, and the
contact's internal-link arrow appears only then. That is how core renders a many2one in a list — the
link button lives in the editable branch of the template, never the readonly one — and how core's
own contact-in-a-tab list behaves, `account.move`'s Journal Items.

Two overrides were considered in September 2026 and dropped: a text cursor (which needs
`!important`, because the list renderer's `cursor-pointer` utility is declared that way), and a
custom cell widget rendering the link arrow on hover. The second is not a core pattern anywhere, so
it would be ours to keep working across Odoo upgrades, for a module we may sell. Revisit if the
missing arrow actually costs anyone time.

### Other decisions

**Prefixed field names.** `vmk_host_ids`, not `host_ids`. Field names on a core model are a shared
namespace: another module defining `host_ids` with a different type on `event.event` would break
installs that have both.

**One line per contact per event, enforced in Python, not SQL** (18.0.1.1.1). The obvious
`unique(event_id, partner_id)` constraint shipped in the first release, and armed a trap in the
contact merge wizard. `_update_foreign_keys_generic` (`base/wizard/base_partner_merge.py`) re-points
every foreign key to `res_partner` in raw SQL. On 18 it never asks whether a constraint exists (that
check came later): a table with more than one other column, as this one has, always takes one bulk
`UPDATE` in a savepoint whose error handler falls back to
`DELETE FROM vmk_event_host WHERE partner_id IN <every merged id>`. The unique constraint is what
made that `UPDATE` fail. So merging two contacts who co-hosted one event deleted every host line the
merged contact had, on every event, while the many2many mirror, re-pointed by a different path,
still listed the survivor there. `_check_partner_unique` refuses a duplicate as a `ValidationError`
instead, and the bulk `UPDATE`, which compares no values, is followed by `_vmk_dedupe` from an
override of the wizard's `_merge`: on a shared event the survivor keeps the line that was its own
before the merge, with its role and position, and the merged contact's goes, as the merge keeps the
survivor's name and email; and every event it hosts recomputes its mirror and summary, which the raw
SQL left stale. Which lines are whose is read before `super()`, since the SQL then points them all
at the survivor. Upgrading drops the SQL constraint: Odoo records each one as an
`ir.model.constraint` row, and at the end of an upgrade drops any the module no longer declares (the
log says `Dropped CONSTRAINT vmk_event_host_partner_event_uniq`). `tests/test_event_host.py` merges
co-hosts to prove both.

**The merge bookkeeping runs as superuser** (18.0.1.1.1). The wizard is granted to
`base.group_partner_manager`, who need no Events group and have no access to `vmk.event.host`, so
the override's search and `_vmk_dedupe` raised an AccessError on every contact merge once the module
was installed. And a user in an Events group sees only their companies' events, so a dedupe run as
them could miss the survivor's duplicate lines on an event of another company. Core's own `_merge`
does its bookkeeping the same way (raw SQL for the foreign keys, and `.sudo()` searches and writes
in `_update_reference_fields_generic`, `base_partner_merge.py:175-183`), so the capture and the
dedupe go through `sudo()` too. `tests/test_access.py` merges as a partner manager outside Events
and as an event user of another company. Both also hold `base.group_erp_manager`, because 18's
`_update_values` (`base_partner_merge.py:337`) reads every field of the contacts, and `signup_type`
(`auth_signup`, `groups="base.group_erp_manager"`) raises an AccessError for anyone else: on 18 a
partner manager who is not also an administrator cannot merge at all. 19 skips fields that are not
copied.

**A line's name is read as superuser** (18.0.1.1.1). `vmk.event.host._compute_display_name` reads
`partner_id.sudo().display_name`, as the ORM does for any many2one (`Many2one.convert_to_read`,
`odoo/fields.py:3356`): whether a user may see a host is decided by the line and its event, not by
the contact's own record rule. In a multi-company database a host contact of company A on a shared
event is hidden from a user of company B, and the line's name and the event's host summary, which
reads it, raised an AccessError, so the event form would not open.

**A contact cannot be deleted while it hosts an event.** `partner_id` is required, so its `ondelete`
defaults to `restrict` (`odoo/fields.py:3258-3263`), and the database refuses the delete until the
host line is removed or the contact archived. Core's registrations behave differently: their
`partner_id` is optional, so it is `set null`. Cascading instead would silently shorten an event's
host list, which is a worse surprise than a refused delete.

**Access rights mirror core's own event rules**: read for the registration desk, full rights for
event users and managers. The multi-company record rule mirrors
`event.ir_rule_event_event_ticket_company` — a host line is reachable exactly when its event is.

**Views are anchored on fields and named pages, never on the root tag.**
`<field name="user_id" position="after">` and `<page name="tickets" position="after">` survive core
renaming its own elements; the `<tree>` to `<list>` rename in Odoo 18 broke exactly that kind of
xpath.

### Translations

`i18n/` carries `es` and `ca`, both checked term by term against core's catalogues: `ca` matches
throughout, and `es` but for the one term below. Nineteen more languages are generated, never edited
by hand; see `DEVELOPING.md`. Terms this module shares with core — _Event_, _Sequence_, _Company_,
the ORM's own _Created by_ and _Last Updated on_ — take core's own `msgstr` out of `base`'s and
`event`'s catalogues rather than being translated afresh, so the Hosts tab reads as part of the
backend rather than introducing a second vocabulary. Strings core does not have, such as the host
`help` text, are ours to write.

**One term differs from core 18 in `es`, deliberately.** The field labelled _Host_ keeps
"Anfitrión". Core 18's only Spanish "Host" is Enterprise's `frontdesk` app, an unrelated sense, and
its catalogue reads `"Anfitrión "` with a stray trailing space, which core 19 removed; ours matches
19's, and is declared as an exception for 18 in our catalogue check.

**The module's own name and summary are hand-maintained**, in the POT as well as both PO files.
`ir_module.py` registers every module record as `base.module_<name>`, so the exporter attributes
them to `base` and omits them from our catalogue — and `PoFileReader` merges each PO against its POT
and drops whatever the merge marks obsolete, so a PO entry with no POT counterpart disappears in
silence and the module keeps its English name in a Spanish database.
`tests/test_translations.py::TestModuleNameTranslation` fails loudly if a re-export drops them, and
also asserts the premise the whole workaround rests on: that the xmlid still belongs to `base`.

### Licence: LGPL-3

LGPL-3, as the whole repo is, and for this module it is not optional. Our own proprietary modules
will depend on it: the planned glue module putting a host on each session depends on both this and
`vmk_event_sessions`, which is OPL-1. Odoo's licence-compatibility table (in its
[Apps FAQ](https://apps.odoo.com/apps/faq)) permits an OPL-1 or OEEL-1 module to depend on LGPL-3,
but **not** on AGPL-3, so AGPL here would leave that glue with no licence it could carry.

### Testing

Against a local Odoo 18 with this repo on the addons path, as in
[DEVELOPING.md](../DEVELOPING.md#testing-locally):

```bash
docker compose run --rm odoo odoo -d test --init vmk_event_host \
    --without-demo=all --stop-after-init
docker compose run --rm odoo odoo -d test -u vmk_event_host \
    --test-enable --test-tags /vmk_event_host --stop-after-init
```

**Browser tests.** `tests/test_tours.py` runs tours from `static/tests/tours/` in headless Chrome:
the hosts summary reads in the lines' own order and opens the Hosts tab, adding a host from the tab,
dragging a line by its handle reorders the hosts and the summary, and the events list is searched
and grouped by host (an event with two hosts appears under both). They are tagged `post_install` and
run with the tests above, given a Chrome the Odoo image can find.
