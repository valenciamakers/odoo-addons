# Multi-Day Event Slots (`vmk_event_slot_multiday`)

Allow event slots to span multiple days: a weekend retreat from Friday evening to Sunday afternoon,
an overnight hackathon, or a two-day course offered on several dates. Standard Odoo keeps every slot
within one day; with this module each slot has a start date and an end date, and the slot form shows
them as one range.

**How to use it** is in the user documentation, [`doc/index.rst`](doc/index.rst), which the Odoo
Apps Store also shows on the module's page, together with the changelog.

It needs only the Events app. With Website Events installed as well, the companion module
[`vmk_website_event_slot_multiday`](../vmk_website_event_slot_multiday) installs itself and shows
visitors both days of a multi-day slot. LGPL-3, © 2026 Valencia Makers, SL.

## For developers

What follows is how the module works and why it is built this way: what core does, which of its
methods this relies on, and the traps found on the way.

### What core does

A core `event.slot` is one `date` and two hours on it, `start_hour` and `end_hour`, both in the
event's timezone (`event/models/event_slot.py`). `_compute_datetimes` builds `start_datetime` and
`end_datetime` from them, **both on `date`**, and `_check_hours` requires the end hour to be later
than the start hour. So a core slot can never leave its day: a weekend retreat, an overnight
hackathon, or a two-day course offered on several dates cannot be a slot.

Core's slot form shows only an _Hour range_ — no date at all, since a slot is created by clicking a
day in the slot calendar — and core shows a slot in the **event's** timezone everywhere: the hours
on the form, the slot calendar (`event_slot_calendar_model.js`, `normalizeRecord`), and the name.

### What this changes

**A day count, not an end date.** `vmk_end_day_offset` is how many days after its `date` a slot
ends, 0 for a slot within one day, which is every existing slot on install. Storing the length
rather than the end makes it part of the slot: moving `date` by any route — the form, an import,
core's own code — moves the end with it. A weekend moved a week later is still a weekend, and a
one-day slot moved earlier stays one day.

An end date computed from the date and the count would have been the obvious design, and was the
first one built. It cannot tell a slot whose start moved from one whose end was deliberately set
later, and got it wrong both ways: a one-day slot moved earlier silently became several days long,
and a weekend moved past its old end collapsed to one day and failed core's hour check.

**`vmk_end_date` stays, for reading and convenience.** It is stored and computed from the date and
the count, so it can be listed, searched and grouped, and it can be written: `create` and `write`
turn it into the count **before** anything is stored or checked. An inverse would run too late,
because Odoo checks the other fields of a write before it runs inverses, so an end hour written
alongside would meet core's one-day hour check while the slot was still one day long.

**Given both an end date and a day count, they must agree**, and a disagreement is refused rather
than settled by picking one. Letting the count win was the first rule, and it dropped an explicit
end date in silence the first time another module's `create` filled in the count's default of 0
beside it; the slot then failed core's hour check with a message about hours, not dates.

**The end is computed on the end date.** `_compute_datetimes` calls core and then, for a multi-day
slot only, rebuilds `end_datetime` from `vmk_end_date` and `end_hour` in the event's timezone. That
is the whole change as far as the rest of Odoo is concerned, because everything downstream reads
`end_datetime` rather than `date`:

- the registration's own end (`event.registration.event_end_date`), and so the attendee's calendar
  links and the "after the event" mail scheduler for a slot;
- the slot calendar, which draws the slot across its days;
- core's `_check_time_range`, which keeps a slot inside its event's dates and now sees the real end,
  so a weekend running past the event's end is refused by core's own message.

None of those needed an override, and a test pins the registration's end. Core's `event` and
`website_event` suites pass with this module installed.

**Core's hour check still runs for one-day slots.** `_check_hours` hands one-day slots to core
unchanged and checks a multi-day slot's hours only for being hours: across days, 13:00 on Sunday is
later than 18:00 on Friday, which is exactly what core's check would refuse. An end before the start
gets its own message rather than core's one about hours.

**The name says both days.** Core names a slot by its date and its hour range,
`Oct 9, 2026, 18:00 - 20:00`, which on a slot ending two days later reads as one evening. A
multi-day slot is named `Oct 9, 2026, 18:00 - Oct 11, 2026, 13:00` instead, in the formats core uses
(`format_date` medium, `format_time` short). A one-day slot keeps core's name. Core's seats suffix,
"(Sold out)" and the like, is added only when the event is _not_ multi-slot, so it never reaches a
slot in use and replacing the whole name loses nothing.

### The slot form: one range, in the event's timezone

**One _Date_ row, start to end**, in place of core's _Hour range_:
`Oct 9, 6:00 PM → Oct 11, 1:00 PM`, the same shape as the event form's own dates. Core's hour row is
hidden rather than removed, because other modules anchor on it. The slot list gains an optional End
Date column.

**Shown in the event's timezone, not the viewer's.** A datetime field shows the viewer's own time,
which for anyone editing from another timezone would disagree with the slot calendar, the slot's
name, and core's hours — all in event time. So the row carries core's own help from the hours,
"Expressed in the event timezone."

**The widget, `vmk_event_slot_daterange`, does what core's slot calendar does.** To show a slot,
core's calendar converts its datetimes to the event's zone and relabels them local, keeping the
wall-clock time (`normalizeRecord`). To save one, it writes `date`, `start_hour` and `end_hour` from
that wall-clock time, never the datetimes (`buildRawRecord`). The widget does both around core's own
`DateTimeField`, which it uses unchanged: it hands the field a view of the record in which the range
reads as event time, and in which updating the range writes the slot's date, hours and day count.

**The widget declares those four fields itself, flagged for onchange.** The server marks a field for
onchange only where a view's arch declares it, and it is the onchange that recomputes the datetimes
the range shows. Declared only by the widget, an edit to the range made the form dirty but left it
showing the old dates until saved. `vmk_event_sessions` happens to put `date` in the slot form,
which hid this on a database with it installed; the check on a database with only core's event
modules found it.

So the datetimes stay read-only computed fields on the model, as in core, and the server has no
datetime handling of its own. That matters: core's slot calendar creates slots with the datetimes in
the vals **as well as** the date and hours, relying on the datetimes being ignored. Making them
writable on the model would have shifted every click-created slot for a viewer outside the event's
timezone.

**One guard that the form made necessary.** Core's `_compute_datetimes` fails on a slot with no date
or no event timezone yet, such as a new slot opened without an event. Core's form never asks for the
datetimes, so core never meets that; ours shows them, so the override leaves such a slot's datetimes
empty instead.

**This leans on core's web client internals.** The widget relies on `DateTimeField` reading the
record through `record.data` and writing through `record.update`, and on `dateRangeField`'s
`extractProps` and `fieldDependencies`, all in
`web/static/src/views/fields/datetime/ datetime_field.js`. A change there breaks the widget loudly
rather than quietly — the form fails to render — but re-check it on any major upgrade.

### What it does not do

**Dragging a slot in the calendar.** Core's slot calendar cannot move slots at all (its `date_start`
is the computed `start_datetime`, which the calendar needs writable), and this module leaves that as
it is. Edit the range on the form.

**The public event page's slot picker.** Core lists slots under the day they start, as a button
showing the start time. A multi-day slot therefore appears under its first day. Once a visitor picks
it, `vmk_website_event_slot_multiday` prints both days in the registration modal; the button itself
is unchanged.

**Event dates.** Core does not widen an event to fit its slots, and neither does this. Set the
event's dates to cover the slots first; core refuses a slot that falls outside them.

### Translations

`i18n/` carries `es` and `ca`, and `./odev terms vmk_event_slot_multiday` reports both clean against
core. _Date_, _End Date_, _Event Slot_, _Display Name_ and core's timezone help take core's own
`msgstr`, so the new row reads as part of core's form. Catalan's core catalogue leaves the timezone
help empty, so that one is ours.

**The module's own name and summary are hand-maintained**, in the POT as well as both PO files.
`ir_module.py` registers every module record as `base.module_<name>`, so the exporter attributes
them to `base` and omits them from our catalogue — and `PoFileReader` merges each PO against its POT
and drops whatever the merge marks obsolete, so a PO entry with no POT counterpart disappears in
silence. `tests/test_translations.py::TestModuleNameTranslation` fails loudly if a re-export drops
them. Those entries are kept on one line each, because the test reads them that way.

### Licence: LGPL-3

LGPL-3, as the whole repo is, and for this module it is not optional. Our own proprietary
`vmk_event_sessions` (sessions under an event, OPL-1) depends on it: a slot holding several sessions
spans all of them, which is a multi-day slot. Odoo's licence-compatibility table (in its
[Apps FAQ](https://apps.odoo.com/apps/faq)) lets an OPL-1 module depend on LGPL-3 but not on AGPL-3.
It is also plainly a gap in core that other modules may want to build on.

### Testing

```bash
cd "../Tech Stack/odoo-dev"
./odev install vmk_event_slot_multiday
./odev test vmk_event_slot_multiday
```

Fifteen tests on the model and form arch, three on translations. The names are checked by formatting
the expected dates with the same helpers, so the tests pass in any language's date format.

**The widget needs a browser**, which the `odoo:19` image has not, so it was checked by hand in
Chrome with the event in `America/New_York` and the browser in `Europe/Madrid`: the range showed
event time, and editing, moving, and creating a slot through it stored the right date, hours and day
count. Core's `event` and `website_event` suites were run with the module installed on two fresh
databases: one with only core's event modules, and one with our `vmk_event_sessions` and
`vmk_website_event_sessions` as well.
