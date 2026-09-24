# Website Multi-Day Slots (`vmk_website_event_slot_multiday`)

Allow event slots to span multiple days, on the website too: a weekend retreat from Friday evening
to Sunday afternoon, an overnight hackathon, or a two-day course offered on several dates. It
includes [`vmk_event_slot_multiday`](../vmk_event_slot_multiday), which gives each slot a start date
and an end date, and adds the website half: when a visitor selects a slot that ends on a later day,
the registration modal shows both dates.

**How to use it** is in the user documentation, [`doc/index.rst`](doc/index.rst), which the Odoo
Apps Store also shows on the module's page, together with the changelog.

It requires the Events app, which in Odoo 19 is `website_event`. From the Apps Store this is the
module website users download: it depends on `vmk_event_slot_multiday`, so the store includes both.
LGPL-3, © 2026 Valencia Makers, SL.

## For developers

What follows is how the module works: what core does, the patch this applies, and what to re-check
on an upgrade.

Depends on `vmk_event_slot_multiday` and `website_event`, and is `auto_install`. Odoo auto-installs
a module only while one of its dependencies is being installed (`button_install` in
`base/models/ir_module.py`), so in a clone of this repo it arrives with whichever of the two is
installed last, and a backend-only database never sees it. A copy added to an addons path after both
are installed is installed by hand.

### What it changes

Core's registration modal, once a slot is picked, prints a "Selected Date" line built in
`website_event/static/src/interactions/website_event_slot_details.js`, `_onSlotSelected`: the slot's
start as a date and time, and its end **as a time alone**, since a core slot never leaves its day.
For a slot from Friday 18:00 to Sunday 13:00 that reads `Fri, Oct 9, 2026, 6:00 PM - 1:00 PM` — one
evening.

A patch on `SlotDetails.prototype._onSlotSelected` lets core run, then, only where the slot's start
and end fall on different days in the event's timezone, rewrites the line with a date on both ends:
`Fri, Oct 9, 2026, 6:00 PM - Sun, Oct 11, 2026, 1:00 PM`. It uses core's own format for the start,
`DATETIME_MED_WITH_WEEKDAY`, and the same for the end. A one-day slot keeps core's line exactly.

**No template change was needed.** Core already puts the slot's `start_datetime` and `end_datetime`
on each button as `data-slot-start` and `data-slot-end`, and `vmk_event_slot_multiday` makes
`end_datetime` the real end, so the patch only has to format what is there.

### What it does not change

**The slot buttons.** Core lists slots under the day they start, each button showing its start time,
so a multi-day slot appears under its first day as `6:00 PM`. The modal line above is where the end
is said. A button showing a span would change core's layout for every slot, and is left until
someone needs it.

### Patches break quietly

When Odoo renames `SlotDetails`, moves its file, or renames `_onSlotSelected` or
`selectedSlotDatetime`, the patch either fails to load (a renamed import breaks the frontend bundle
loudly) or stops applying with nothing raised, and the modal returns to core's one-day line.
Re-check the three names above on any major upgrade.

### Translations

The module adds no text of its own; the line is formatted by Luxon in the visitor's language.
`i18n/` carries `es` and `ca` for the module's own name and summary, hand-maintained for the reason
given in `../vmk_event_slot_multiday/README.md`, and `tests/test_translations.py` guards them.

### Licence

LGPL-3, as `vmk_event_slot_multiday` is; see its README.

### Testing

```bash
cd "../Tech Stack/odoo-dev"
./odev install vmk_website_event_slot_multiday
./odev test vmk_website_event_slot_multiday
```

The tests cover the translations only. The patch itself needs a browser, which the `odoo:19` image
has not, so it was checked by hand in Chrome against a Friday-to-Sunday slot and a one-day slot on
the same event.
