=====================
Multi-Day Event Slots
=====================

Allow event slots to span multiple days: a weekend retreat from Friday evening to Sunday
afternoon, an overnight hackathon, or a two-day course offered on several dates.

In standard Odoo, an event slot must start and end on the same day, so it can never span more
than one. This module gives each slot a start date and an end date, so it can span as many days as
it needs.

Installation
============

Install **Multi-Day Event Slots** from the Apps menu. It only requires the **Events** app.

If the **Website Events** module is also installed, the companion **Website Multi-Day Slots**
module installs automatically, and displays the start and end dates to website visitors when
they select a slot.

Existing slots are left unchanged until you give them a later end date.

Using it
========

Slots belong to events with **Multiple Slots** enabled on the event form.

#. Open an event and click the slot count beside **Multiple Slots** to see its slots.
#. Create a slot by clicking a day in the calendar, or open an existing one.
#. On the slot form, the **Date** row shows the slot's start and end together, the same way the
   event form does. Click the end and pick a later date, such as Friday 18:00 to Sunday 13:00.
#. Save. The slot calendar now draws the slot across all its days.

**Times are in the event's timezone, not yours**, as Odoo already does for slots. The slot form
displays the timezone just under the Date row.

**Moving a slot keeps its length.** Move a multi-day slot to another start date and the end date
moves with it.

**The rest of Odoo sees the whole slot.** An attendee's registration ends when the slot does, so
calendar links include all days. Mail scheduled for after the event is sent once the slot ends.
A multi-day slot is named by its range, for example *9 Oct 2026, 18:00 - 11 Oct 2026, 13:00*.

Limits
======

- **Slots cannot be dragged on the calendar.** This is standard Odoo behaviour. Change the dates on
  the slot form instead.
- **The event's own dates must cover its slots.** Odoo refuses to save a slot that ends after the
  event does, so extend the event first.
- **On the website, a multi-day slot is listed under its first day**, with its start time, the same
  way Odoo lists every slot. The registration modal window shows both days once a visitor selects one.

Changelog
=========

19.0.1.0.1 (24 September 2026)
------------------------------

- Licensed LGPL-3, and credited to Valencia Makers. No change in behaviour.

19.0.1.0.0 (24 September 2026)
------------------------------

- First release. Slots can span multiple dates; the slot form shows one start-to-end range in the
  event's timezone; registrations, calendars, and scheduled mail all use the slot's end date.
