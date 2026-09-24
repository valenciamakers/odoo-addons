Alphabetical order on the Apps page, sorted by the name shown on the card.

In standard Odoo, the Apps page is ordered by the hidden technical name of each app, so Employees
is filed under *hr* and Invoicing under *account*. This module orders it by the name on the card,
alphabetically.

**Installation**

Install **Apps Page Sort** from the Apps menu. It only requires Odoo's **base** module, so it works
with any set of apps, on both Community and Enterprise.

**Using it**

There is nothing to configure. Once installed, the Apps page is alphabetical by the name on each
card, in both its card and list views.

**The order follows each user's own language setting.** Case is ignored, and accented names are sorted
correctly.

**Apps are sorted in front of other modules** when you clear the Apps filter, so the page does not mix the
several hundred technical modules in among them.

**Limits**

- **Only the Apps page changes.** Other lists of modules maintain Odoo's default order.
- **Odoo's own curated order on that page is replaced** by alphabetical order.
- **Accented names need ICU in PostgreSQL**, which the standard packages include. Without it, case
  is still ignored, but accented names sort after *Z*.

**Changelog**

*19.0.1.2.0 (24 September 2026)*

- Names are compared alphabetically rather than in the database's byte order, so *CRM* sorts
  after *Calendar* and *Contacts*, and accented names sort beside their letter.

*19.0.1.1.1 (24 September 2026)*

- Licensed LGPL-3, and credited to Valencia Makers. No change in behaviour.

*19.0.1.1.0 (19 August 2026)*

- Licensed AGPL-3, from MIT. No change in behaviour.

*19.0.1.0.0 (13 August 2026)*

- First release. The Apps page's card and list views are ordered by the name on the card.
