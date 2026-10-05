Allow registration only until an event starts, or a set time in advance.

In standard Odoo, registrations stay open until an event **ends**, so users can sign up for an
event that has already started. This module closes registration when an event starts, or at a set
time before, and can be configured on a global or per-event basis.

**Installation**

Install **Event Registration Deadline** from the Apps menu. It requires the **Events** app.

**Using it**

#. Turn it on in the global Events settings, setting a single deadline for every event: go to
   **Events > Configuration > Settings**, turn on **Registration Deadline** under
   **Registration**, and set **Time Before Start**, such as *1h 30m*. Set *0h* to close
   registration when the event starts.
#. Set a custom deadline on individual events, next to the registration limit: open the event,
   tick **Registration Deadline** next to **Limit Registrations**, and set the time before the
   start.

Once the deadline passes, the event's website page shows **Registrations Closed**.

**An event can be given its own deadline even when the global setting is off.**

**Tickets with their own Registration End keep it**; the deadline applies only to tickets without
one.

**On events with multiple slots**, registration closes the same amount of time before each slot
starts, and the event's page shows *Registrations Closed* once it has closed for every slot.

**Limits**

- **Only online registration closes.** The deadline governs the event's website page; your team can
  still add attendees from the backend.
- **A deadline cannot reopen registrations.** It only ever closes them earlier than Odoo would.

**Changelog**

*20.0.1.2.0 (5 October 2026)*

- Translated into nineteen more languages: Chinese (Simplified and Traditional), Czech, Danish,
  Dutch, French, German, Indonesian, Italian, Japanese, Korean, Polish, Portuguese (Brazil and
  Portugal), Romanian, Russian, Swedish, Turkish, and Ukrainian.
- Catalan: *Event Slot* is now translated, as *Franja horària*.

*20.0.1.1.0 (1 October 2026)*

- An event with multiple slots now shows *Registrations Closed* once the deadline has passed for
  every slot. Before, its page kept offering Register, over a pop-up with no dates to choose.
- Browser tests added.

*20.0.1.0.0 (30 September 2026)*

- First release for Odoo 20, ported from 19.0.1.0.4. No change in behaviour.
- The settings help says to set *0h*, not *00:00*, since Odoo 20 shows the time as a duration.
- On the event form the hours take the width of their content, so *2h Before Start* has no gap.

*19.0.1.0.4 (28 September 2026)*

- Catalan: *Config Settings* reads as Odoo's own base module has it. No change in behaviour.

*19.0.1.0.3 (24 September 2026)*

- The setting's help reads "Allow registration only until an event starts", since a free event has
  registrations but no tickets. No change in behaviour.

*19.0.1.0.2 (24 September 2026)*

- Licensed LGPL-3, and credited to Valencia Makers. No change in behaviour.

*19.0.1.0.1 (22 September 2026)*

- The module's name and summary are translated into Spanish and Catalan.

*19.0.1.0.0 (22 September 2026)*

- First release. A global registration deadline in the Events settings, a per-event override,
  and the same rule applied to each slot of a multi-slot event.
