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
- **The duration is `float_time`,** so it takes hours and minutes, which Odoo 20 displays as a
  duration in the user's language: `1h 30m` closes registration ninety minutes before the start, and
  `0h` ends registration at the event start time.
- **On the event form the hours fit their content,** so "2h Before Start" reads as one phrase.
  Core's `o_input_5ch` fixes the input at 5ch, which suited 19's `02:00` but leaves a gap after 20's
  `2h`; `static/src/registration_deadline.scss` sizes it with `field-sizing: content` where the
  browser supports it, and leaves core's width elsewhere.

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

**Multi-slot events, at the event level.** Their `date_begin` is the earliest slot's start, so
closing the event there would stop selling every later slot too. Core handles those per slot — and
so does this module, by extending `_filter_open_slots`. The event itself closes only once the
deadline has reached every one of its slots (20.0.1.1.0). Until then a later slot is still on sale;
after that, the page would offer Register over a pop-up saying "No Future Dates Available". Core has
the same gap from the last slot's start to the event's end, and a deadline widens it by its own
length, on every multi-slot event. An event with no slots yet is left as core has it.

### Slots get the same rule

`website_event` retires a slot whose `start_datetime` has passed
(`website_event/models/event_slot.py:9`, `_filter_open_slots`), with **no lead time**. Left alone,
the policy would apply to single events and not to cohorts: sales stopping ninety minutes early for
one and exactly on the hour for the other. This module tightens that filter with the same deadline.

It only ever tightens. A ticket's Registration End overrides the rule on a single event but not
here: it cannot loosen a deadline core itself applies, and on a multi-slot event a ticket says
nothing about which slot it belongs to.

**This is why the module depends on `website_event` rather than `event`** — half the rule lives in a
method that module defines. On 20 the website templates call it directly
(`website_event/views/event_templates_page_registration.xml:218` and `:686`), so the override
reaches both the preview and the registration modal.

### What changed on Odoo 20

- **`ir.config_parameter` is typed.** `get_param` and `set_param` are gone
  (`base/models/ir_config_parameter.py`), so `_vmk_deadline_hours` reads the switch with `get_bool`
  and the duration with `get_float`. The settings form needs no change: a `config_parameter` boolean
  is stored by `set_bool` and a float by `set_float` (`base/models/res_config.py:322-345`), which
  write `True` and `1.5` as text exactly as 19 did, so a database upgraded from 19 keeps its values.
- **pytz is gone**, so the tests build a slot's local date and hour with `zoneinfo`.
- The `_compute_event_registrations_open` override, the `seats_limited` anchor on the event form and
  the `registration_setting_container` block in Settings are unchanged
  (`event/models/event_event.py:298`, `event/views/event_event_views.xml:86`,
  `event/views/res_config_settings_views.xml:37`). Core relabelled the seat limit "Limit
  Registrations"; nothing of ours copies that wording.

### What it does not depend on

Nothing about sessions. The rule reads `date_begin` for an event and `slot.start_datetime` for a
slot. Where a module makes an event's dates follow a series of sessions — `vmk_event_sessions` does
— `date_begin` is already the first session's start, so a series gets the right behaviour here
without this module knowing sessions exist.

### Translations

`i18n/` carries `es` and `ca`, both checked term by term against core's catalogues. Nineteen more
languages are written by `tools/i18n_fill.py`, never by hand; see `DEVELOPING.md`. Shared terms —
_Event_, _Config Settings_, _Display Name_ — take core's own `msgstr` rather than a fresh
translation. _Event Slot_ is core's row and core's Catalan leaves it untranslated, so ours says
`Franja horària`, as our other slot modules do, rather than showing English (5 October 2026).

**The module's own name and summary** are in the POT as well as both PO files. `ir_module.py`
registers every module record as `base.module_<name>`, so 19's `odoo i18n export` never emitted them
and they were kept by hand. Odoo 20's exporter writes them, under this module, beside a
`description` entry holding the whole README, which we leave out: the store page is `index.html`,
and nothing displays it. `PoFileReader` merges each PO against its POT and drops whatever the merge
marks obsolete, so a PO entry with no POT counterpart disappears in silence and the module keeps its
English name in a Spanish database. `tests/test_translations.py::TestModuleNameTranslation` fails
loudly if a re-export drops them.

### Nothing reaches the chatter, deliberately

Both fields added to `event.event` carry no `tracking`. A deadline is a sales rule, not a fact about
the event anyone will later ask when it changed, and `event.event` already tracks the dates a
deadline is derived from. Writing the override into the chatter would record the setting rather than
the decision, which is the failure mode worth avoiding: a history that logs the side effect instead
of the act. Nothing here calls `message_post` either.

### Testing

Against a local Odoo 20 with this repo on the addons path, as in
[DEVELOPING.md](../DEVELOPING.md#testing-locally):

```bash
docker compose run --rm odoo odoo -d test --init vmk_event_registration_deadline \
    --without-demo=all --stop-after-init
docker compose run --rm odoo odoo -d test -u vmk_event_registration_deadline \
    --test-enable --test-tags /vmk_event_registration_deadline --stop-after-init
```

Thirteen tests: the default, the per-event override, an override of zero, a ticket's Registration
End winning, a ticket without one not winning, a multi-slot event staying open while a slot is still
ahead and closing once none is, and a slot retired by the deadline rather than merely by its start.

**A trap for anyone writing more of them.** `start_hour` on a slot is a clock time in the event's
timezone, not an offset — a literal `10.0` in a test built from `now` lands wherever it lands, and
the first draft of these put slots outside their own events. `_slot()` in the test file converts a
moment into the date and hours core wants.

### Browser tests

`tests/test_tours.py` drives a real browser through `static/tests/tours/`. A visitor on the event
page is shown Register or core's _Registrations Closed_ notice, each case beside its opposite: past
and before the deadline, an event's own deadline looser and tighter than the global one, and a
global switch that is off. On a multi-slot event the registration pop-up offers a later slot but not
one inside the deadline. In the backend, the setting and the per-event field are set and saved
through the interface, and Python then checks the stored values and `event_registrations_open`.
Every date is relative to the run. A multi-slot event whose slots are all inside the deadline is
closed like any other, with the two-slot case beside it as the control. On Odoo 20 the time fields
show durations, so the tours type and expect _3h 30m_ and _1h_ where 19's read _03:30_ and _01:00_.

### Licence

LGPL-3, as the whole repo is. See `LICENSE`.
