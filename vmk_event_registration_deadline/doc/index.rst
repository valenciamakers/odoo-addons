Allow registration only until an event starts, or a set time in advance.

In standard Odoo, registrations stay open until an event **ends**, so people can sign up for a
workshop that is already under way, or a course that is half over. This module closes
registrations when an event starts, or a set time before, for every event or only the ones you
choose.

**Installation**

Install **Event Registration Deadline** from the Apps menu. It requires the **Events** app.

**Using it**

#. Go to **Events > Configuration > Settings**. Under **Registration**, turn on **Registration
   Deadline** and set **Time Before Start**, such as *01:30*. Set *00:00* to close registrations
   when the event starts.
#. To give one event its own deadline, open it and tick **Registration Deadline**, next to
   **Limit Registrations**, then set the time before the start.

Once the deadline passes, the event's website page shows **Registrations Closed**.

**An event's own deadline always applies**, even when the setting is off.

**Tickets keep their own Registration End.** A ticket with a Registration End set follows that date
instead; the deadline only applies to tickets without one.

**Events with multiple slots** close each slot the same time before it starts, rather than closing
the whole event.

**Limits**

- **Only online registration closes.** The deadline governs the event's website page; your team can
  still add attendees from the backend.
- **A deadline cannot reopen registrations.** It only ever closes them earlier than Odoo would.

**Changelog**

*19.0.1.0.2 (24 September 2026)*

- Licensed LGPL-3, and credited to Valencia Makers. No change in behaviour.

*19.0.1.0.1 (22 September 2026)*

- The module's name and summary are translated into Spanish and Catalan.

*19.0.1.0.0 (22 September 2026)*

- First release. A global registration deadline in the Events settings, a per-event override,
  and the same rule applied to each slot of a multi-slot event.
