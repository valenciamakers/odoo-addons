# Event Registration Deadline (`vmk_event_registration_deadline`)

Allow registration only until an event starts, or a set time in advance. Standard Odoo keeps
registrations open until an event ends; this module closes them at the start, or a set time before,
globally or per event.

**How to use it** is in the user documentation, [`doc/index.rst`](doc/index.rst), which the Odoo
Apps Store also shows on the module's page, together with the changelog.

It depends on `website_event` (the _Events_ app). LGPL-3, © 2026 Valencia Makers, SL.

## For developers

### Why

Core decides whether registration is open in `event.event._compute_event_registrations_open`, and
the only test it makes against the event's own dates is **`date_end >= now`**. There is no reference
to `date_begin` anywhere in that computation. So a nine-to-five workshop is still on sale at 16:55,
and a four-week course can be bought in week three with three weeks already missed.

That is reasonable for a conference, where arriving on day two is normal. It is wrong for anything
taught. Core offers a per-ticket _Registration End_ to handle it, but that has to be set on every
ticket of every event, and the failure mode of forgetting is selling somebody a course that has
already happened.

### What it does

A deadline, expressed as a duration before the event starts:

- **A switch in Settings → Events → Registration**, with the duration beside it. Off by default, so
  installing the module changes nothing until somebody turns it on — core gates a feature inside an
  installed module the same way, with `use_event_barcode` on this very page and `use_invoice_terms`
  in `account`.
- **The duration is `float_time`,** so it takes hours and minutes: `1:30` closes registration ninety
  minutes before the start. `00:00` ends registration at the event start time.

The duration field carries no `help` in Settings: a `<setting>` labels its own fields and does not
give them the `?` a form label would, so anything written there is never seen. What needed saying
moved into the setting's own help, which renders as the muted line under the title.

- **A per-event override**, beside the seat limit on the event form. A checkbox turns it on, the way
  core pairs `seats_limited` with `seats_max` — a float alone could not express "no override",
  because zero is a real setting.

An event that sets its own deadline is opted in whatever the global switch says. The switch means
"apply a deadline to events by default", and an event asking for one has answered for itself — so
turning the feature off stops it applying everywhere it was implicit, and nowhere it was asked for.

### What it deliberately leaves alone

**A ticket that defines its own Registration End.** Core's `is_expired` is False whenever
`end_sale_datetime` is blank, so blank is the case this module is for. A date somebody typed is a
deliberate choice to allow late registration, and it wins.

### What Odoo 18 does not have

**No per-slot deadline.** `event.slot` and multi-slot events (`is_multi_slots`) are new in Odoo 19;
Odoo 18 has neither, so there is nothing to apply the rule to beyond a single event's own
`date_begin`. The 19 module also tightens `website_event`'s `_filter_open_slots` for exactly this
reason; that half does not exist here, and neither does `models/event_slot.py`. **This 18.0 port is
event-level only.**

**Why the module still depends on `website_event` rather than `event`.** `event_registrations_open`
is a plain `event` field — `event/models/event_event.py`, `_compute_event_registrations_open` — but
the only place it visibly does anything is `website_event`'s registration templates
(`event_templates_page_registration.xml` and the event list/page templates), which show
**Registrations Closed** and hide the **Register** button once it is false. Without `website_event`
installed, closing the field changes nothing a user can see.

### What it does not depend on

Nothing about sessions. The rule reads `date_begin` for an event. Where a module makes an event's
dates follow a series of sessions — `vmk_event_sessions` does, on Odoo 19 — `date_begin` is already
the first session's start, so a series gets the right behaviour here without this module knowing
sessions exist.

### Translations

`i18n/` carries `es` and `ca`, both checked term by term against core's catalogues. Nineteen more
languages are written by `tools/i18n_fill.py`, never by hand; see `DEVELOPING.md`. Shared terms —
_Event_ and _Config Settings_ — take core's own `msgstr` rather than a fresh translation. (The 19.0
module's catalogue also carries _Display Name_, _ID_, and _Event Slot_; Odoo 18's exporter no longer
attributes `display_name`/`id` to an inheriting module, and this port has no `event.slot` model, so
all three entries are gone here.)

**The module's own name and summary are hand-maintained**, in the POT as well as both PO files.
`ir_module.py` registers every module record as `base.module_<name>`, so `odoo i18n export` never
emits them — and `PoFileReader` merges each PO against its POT and drops whatever the merge marks
obsolete, so a PO entry with no POT counterpart disappears in silence and the module keeps its
English name in a Spanish database. `tests/test_translations.py::TestModuleNameTranslation` fails
loudly if a re-export drops them.

### Nothing reaches the chatter, deliberately

Both fields added to `event.event` carry no `tracking`. A deadline is a sales rule, not a fact about
the event anyone will later ask when it changed, and `event.event` already tracks the dates a
deadline is derived from. Writing the override into the chatter would record the setting rather than
the decision, which is the failure mode worth avoiding: a history that logs the side effect instead
of the act. Nothing here calls `message_post` either.

### Testing

Against a local Odoo 18 with this repo on the addons path, as in
[DEVELOPING.md](../DEVELOPING.md#testing-locally):

```bash
docker compose run --rm odoo odoo -d test --init vmk_event_registration_deadline \
    --without-demo=all --stop-after-init
docker compose run --rm odoo odoo -d test -u vmk_event_registration_deadline \
    --test-enable --test-tags /vmk_event_registration_deadline --stop-after-init
```

Nine tests: the default, the per-event override, an override of zero, a ticket's Registration End
winning, and a ticket without one not winning. The 19.0 module's two slot tests are gone with
`event_slot.py` — see [What Odoo 18 does not have](#what-odoo-18-does-not-have).

### Browser tests

`tests/test_tours.py` drives a real browser through `static/tests/tours/`. A visitor on the event
page is shown Register or core's _Registrations Closed_ notice, each case beside its opposite: past
and before the deadline, an event's own deadline looser and tighter than the global one, and a
global switch that is off. In the backend, the setting and the per-event field are set and saved
through the interface, and Python then checks the stored values and `event_registrations_open`.
Every date is relative to the run. The 19.0 tours for multi-slot events (the registration pop-up
offering a later slot, and an event closing once every slot is past the deadline) are not here, for
the reason in [What Odoo 18 does not have](#what-odoo-18-does-not-have).

**One thing the tests do for 18.** With `website_event` installed, core's event onboarding tour
starts on its own for the admin, and one of its steps carries a key (`noPrepend`) that 18's step
schema rejects, which fails whatever tour is running. The test class switches the admin's onboarding
off, as core's own UI tests do.

### Licence

LGPL-3, as the whole repo is. See `LICENSE`.
