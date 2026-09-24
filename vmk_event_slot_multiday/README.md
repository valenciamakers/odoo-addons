# Multi-Day Event Slots (`vmk_event_slot_multiday`)

Lets an event slot end on a later day than it starts, so a slot can run from Friday 18:00 to Sunday
13:00. Adds one field, **End Date** (`vmk_end_date`), and changes nothing for a slot that stays
within its day.

## What core does

A core `event.slot` is one `date` and two hours on it, `start_hour` and `end_hour`, both in the
event's timezone (`event/models/event_slot.py`). `_compute_datetimes` builds `start_datetime` and
`end_datetime` from them, **both on `date`**, and `_check_hours` requires the end hour to be later
than the start hour. So a core slot can never leave its day: a weekend retreat, an overnight
hackathon, or a two-day course offered on several dates cannot be a slot.

## What this changes

**An end date beside the date.** `vmk_end_date` is stored and computed from `date`, so every slot
has one: on install every existing slot gets its own date, and is exactly the one-day slot it was.
The compute only fills a missing end or one that `date` has moved past; a later end, once set, is
kept, and that is what makes a slot multi-day.

**The end is computed on the end date.** `_compute_datetimes` calls core and then, for a multi-day
slot only, rebuilds `end_datetime` from `vmk_end_date` and `end_hour` in the event's timezone. That
is the whole change as far as the rest of Odoo is concerned, because everything downstream reads
`end_datetime` rather than `date`:

- the registration's own end (`event.registration.event_end_date`), and so the attendee's calendar
  links and the "after the event" mail scheduler for a slot;
- the slot calendar, which draws the slot across its days;
- core's `_check_time_range`, which keeps a slot inside its event's dates and now sees the real end,
  so a weekend running past the event's end is refused by core's own message.

None of those needed an override, and a test pins the registration's end.

**Core's hour check still runs for one-day slots.** `_check_hours` is overridden to hand one-day
slots to core unchanged and check a multi-day slot's hours only for being hours: across days, 13:00
on Sunday is later than 18:00 on Friday, which is precisely what core's check would refuse. The
hours still sit in 0:00–23:59, with core's own message. A separate constraint refuses an end date
earlier than the date.

**Moving a slot keeps its length.** Writing a new `date` alone moves a multi-day slot's end date by
as many days, so the weekend moved a week later is still Friday to Sunday. A one-day slot stays one
day. Writing both dates at once is taken as written.

**The name says both days.** Core names a slot by its date and its hour range,
`Oct 9, 2026, 18:00 - 20:00`, which on a slot ending two days later reads as one evening. A
multi-day slot is named `Oct 9, 2026, 18:00 - Oct 11, 2026, 13:00` instead, in the formats core uses
(`format_date` medium, `format_time` short). A one-day slot keeps core's name. Core's seats suffix,
"(Sold out)" and the like, is added only when the event is _not_ multi-slot, so it never reaches a
slot in use and replacing the whole name loses nothing.

**The form shows the date at all.** Core's slot form has no date field — a slot is created by
clicking a day in the slot calendar, and after that the form never says which day it is on. A
multi-day slot needs both days in front of whoever edits it, so they sit above core's _Hour range_
as a _Date range_ row in the same shape. The slot list gains an optional End Date column.

## What it does not do

**Dragging a slot in the calendar.** Core's slot calendar cannot move slots at all (its `date_start`
is the computed `start_datetime`, which the calendar needs writable), and this module leaves that as
it is. Edit the dates on the form.

**The public event page's slot picker.** Core lists slots under the day they start, as a button
showing the start time. A multi-day slot therefore appears under its first day. Once a visitor picks
it, `vmk_website_event_slot_multiday` prints both days in the registration modal; the button itself
is unchanged.

**Event dates.** Core does not widen an event to fit its slots, and neither does this. Set the
event's dates to cover the slots first; core refuses a slot that falls outside them.

## Translations

`i18n/` carries `es` and `ca`, and `./odev terms vmk_event_slot_multiday` reports both clean against
core. _End Date_, _Date range_, _Event Slot_ and _Display Name_ take core's own `msgstr`, so the new
row reads as part of core's form.

**The module's own name and summary are hand-maintained**, in the POT as well as both PO files.
`ir_module.py` registers every module record as `base.module_<name>`, so the exporter attributes
them to `base` and omits them from our catalogue — and `PoFileReader` merges each PO against its POT
and drops whatever the merge marks obsolete, so a PO entry with no POT counterpart disappears in
silence. `tests/test_translations.py::TestModuleNameTranslation` fails loudly if a re-export drops
them. Those entries are kept on one line each, because the test reads them that way.

## Licence: LGPL-3, not this repo's AGPL-3 default

Our own proprietary `vmk_event_sessions` (sessions under an event, OPL-1) is meant to build on this:
a slot holding several sessions spans all of them, which is a multi-day slot. Odoo's
licence-compatibility table (in its [Apps FAQ](https://apps.odoo.com/apps/faq)) lets an OPL-1 module
depend on LGPL-3 but not on AGPL-3, so AGPL here would rule that out. It is also plainly a gap in
core that other modules may want to build on, which is the repo's other reason for LGPL.

## Testing

```bash
cd "../Tech Stack/odoo-dev"
./odev install vmk_event_slot_multiday
./odev test vmk_event_slot_multiday
```

Eleven tests on the model and form, three on translations. The names are checked by formatting the
expected dates with the same helpers, so the tests pass in any language's date format.
