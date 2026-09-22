# Event Registration Deadline

Sells tickets only until an event starts, or a set time in advance.

## Why

Core decides whether registration is open in `event.event._compute_event_registrations_open`, and
the only test it makes against the event's own dates is **`date_end >= now`**. There is no reference
to `date_begin` anywhere in that computation. So a nine-to-five workshop is still on sale at 16:55,
and a four-week course can be bought in week three with three weeks already missed.

That is reasonable for a conference, where arriving on day two is normal. It is wrong for anything
taught. Core offers a per-ticket _Registration End_ to handle it, but that has to be set on every
ticket of every event, and the failure mode of forgetting is selling somebody a course that has
already happened.

## What it does

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

## What it deliberately leaves alone

**A ticket that defines its own Registration End.** Core's `is_expired` is False whenever
`end_sale_datetime` is blank, so blank is the case this module is for. A date somebody typed is a
deliberate choice to allow late registration, and it wins.

**Multi-slot events, at the event level.** Their `date_begin` is the earliest slot's start, so
closing the event there would stop selling every later slot too. Core handles those per slot — and
so does this module, by extending `_filter_open_slots`.

## Slots get the same rule

`website_event` retires a slot whose `start_datetime` has passed
(`website_event/models/event_slot.py`, `_filter_open_slots`), with **no lead time**. Left alone, the
policy would apply to single events and not to cohorts: sales stopping ninety minutes early for one
and exactly on the hour for the other. This module tightens that filter with the same deadline.

It only ever tightens. A ticket's Registration End overrides the rule on a single event but not
here: it cannot loosen a deadline core itself applies, and on a multi-slot event a ticket says
nothing about which slot it belongs to.

**This is why the module depends on `website_event` rather than `event`** — half the rule lives in a
method that module defines.

## What it does not depend on

Nothing about sessions. The rule reads `date_begin` for an event and `slot.start_datetime` for a
slot. Where a module makes an event's dates follow a series of sessions — `vmk_event_sessions` does
— `date_begin` is already the first session's start, so a series gets the right behaviour here
without this module knowing sessions exist.

## Translations

`i18n/` carries `es` and `ca`, and `./odev terms vmk_event_registration_deadline` reports both clean
against core. Shared terms — _Event_, _Config Settings_, _Display Name_ — take core's own `msgstr`
rather than a fresh translation. _Event Slot_ is core's row and core's Catalan leaves it
untranslated, so ours stays empty rather than asserting a value on a record we do not own.

**The module's own name and summary are hand-maintained**, in the POT as well as both PO files.
`ir_module.py` registers every module record as `base.module_<name>`, so `odoo i18n export` never
emits them — and `PoFileReader` merges each PO against its POT and drops whatever the merge marks
obsolete, so a PO entry with no POT counterpart disappears in silence and the module keeps its
English name in a Spanish database. `tests/test_translations.py::TestModuleNameTranslation` fails
loudly if a re-export drops them.

## Nothing reaches the chatter, deliberately

Both fields added to `event.event` carry no `tracking`. A deadline is a sales rule, not a fact about
the event anyone will later ask when it changed, and `event.event` already tracks the dates a
deadline is derived from. Writing the override into the chatter would record the setting rather than
the decision, which is the failure mode worth avoiding: a history that logs the side effect instead
of the act. Nothing here calls `message_post` either.

## Testing

```bash
cd ../../Tech\ Stack/odoo-dev
./odev test vmk_event_registration_deadline
```

Nine tests: the default, the per-event override, an override of zero, a ticket's Registration End
winning, a ticket without one not winning, a multi-slot event being left to its slots, and a slot
retired by the deadline rather than merely by its start.

**A trap for anyone writing more of them.** `start_hour` on a slot is a clock time in the event's
timezone, not an offset — a literal `10.0` in a test built from `now` lands wherever it lands, and
the first draft of these put slots outside their own events. `_slot()` in the test file converts a
moment into the date and hours core wants.

## Licence

AGPL-3. See `LICENSE`.
