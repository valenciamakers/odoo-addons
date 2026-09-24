Record who runs an event, as one or more contacts: the instructors, speakers, and facilitators
who host each event.

In standard Odoo, an event records an **Organizer** (the company organizing it), and a
**Responsible** user (who owns the record), but not the people who actually run it. This module
adds these people to the event as contacts, each with an optional role, in an order you set.

**Installation**

Install **Event Hosts** from the Apps menu. It only requires **Events Organization**, the backend
part of the **Events** app.

**Using it**

#. Open an event and go to its **Hosts** tab, or click **Hosts** on the form to jump there.
#. Click **Add a line**, choose a contact, and optionally give them a **Role**, such as *Lead
   Instructor*.
#. Drag the handle at the start of a row to change the order. The **Hosts** summary lists the
   hosts in the same order, along with their roles.

**Finding events by host.** In the events list, search for a host, or use **Group By > Host**. An
event with two hosts will appear under each of them. The optional **Hosts** column lists all hosts
for each event.

**Changes are tracked.** Adding or removing a host is logged in the event's chatter, just like
changes to the Responsible and Organizer fields.

**Limits**

- **Search, grouping, and the list's Hosts column show hosts alphabetically.** Only the Hosts tab
  and the summary on the event form keep the order you set.
- **A contact can be a host only once per event**, and with a single role.
- **Hosts are not shown on the website.** They are recorded in the backend only.

**Changelog**

*19.0.1.0.2 (24 September 2026)*

- Licensed LGPL-3, and credited to Valencia Makers. No change in behaviour.

*19.0.1.0.1 (22 September 2026)*

- A test now keeps the module's name and summary translated in Spanish and Catalan. No change in
  behaviour.

*19.0.1.0.0 (20 September 2026)*

- First release. Hosts on events as ordered contacts with roles; a summary on the event form that
  opens the Hosts tab; and searching, grouping, and tracking by host.
