Allow registration only until an event starts, or a set time in advance.

In standard Odoo, registrations stay open until an event **ends**, so users can sign up for an
event that has already started. This module closes registration when an event starts, or at a set
time before, and can be configured on a global or per-event basis.

**Installation**

Install **Event Registration Deadline** from the Apps menu. It requires the **Events** app.

**Using it**

#. Turn it on in the global Events settings, setting a single deadline for every event: go to
   **Events > Configuration > Settings**, turn on **Registration Deadline** under
   **Registration**, and set **Time Before Start**, such as *01:30*. Set *00:00* to close
   registration when the event starts.
#. Set a custom deadline on individual events, next to the registration limit: open the event,
   tick **Registration Deadline** next to **Limit Registrations**, and set the time before the
   start.

Once the deadline passes, the event's website page shows **Registrations Closed**.

**An event can be given its own deadline even when the global setting is off.**

**Tickets with their own Registration End keep it**; the deadline applies only to tickets without
one.

**On events with multiple slots**, registration closes the same amount of time before each slot
starts.

**Limits**

- **Only online registration closes.** The deadline governs the event's website page; your team can
  still add attendees from the backend.
- **A deadline cannot reopen registrations.** It only ever closes them earlier than Odoo would.

**Changelog**

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
