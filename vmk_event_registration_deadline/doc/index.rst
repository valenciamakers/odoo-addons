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

**Limits**

- **Only online registration closes.** The deadline governs the event's website page; your team can
  still add attendees from the backend.
- **A deadline cannot reopen registrations.** It only ever closes them earlier than Odoo would.
- **No per-slot deadline on Odoo 18.** Multi-slot events are new in Odoo 19, so this build applies
  the rule to a single event's own start only.

**Languages**

Catalan, Chinese (Simplified and Traditional), Czech, Danish, Dutch, English, French, German,
Indonesian, Italian, Japanese, Korean, Polish, Portuguese (Brazil and Portugal), Romanian,
Russian, Spanish, Swedish, Turkish, and Ukrainian. If any translation seems incorrect, please
`contact us <mailto:info@valenciamakers.es>`_ and we will fix it.

**Changelog**

*18.0.1.1.0 (5 October 2026)*

- Translated into nineteen more languages: Chinese (Simplified and Traditional), Czech, Danish,
  Dutch, French, German, Indonesian, Italian, Japanese, Korean, Polish, Portuguese (Brazil and
  Portugal), Romanian, Russian, Swedish, Turkish, and Ukrainian.

*18.0.1.0.1 (1 October 2026)*

- Browser tests added. No change in behaviour.

*18.0.1.0.0 (28 September 2026)*

- First release for Odoo 18, ported from 19.0.1.0.3. Odoo 18 has no multi-slot events, so this
  build has no per-slot deadline: only the global setting and the per-event override.
