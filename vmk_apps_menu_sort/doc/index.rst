Alphabetical order for the apps menu, with Apps and Settings at the end.

In standard Odoo, apps are listed in whatever order they set for themselves, so the apps grid reads
as no order at all. This module lists them alphabetically, with **Apps** and **Settings** kept
at the end.

**Installation**

Install **Apps Menu Sort** from the Apps menu. It only requires Odoo's **base** module, so it works
with any set of apps, on both Community and Enterprise.

**Using it**

There is nothing to configure. Once installed, every list of your apps is alphabetical:

- the apps grid on the home screen, on Enterprise
- the navbar apps menu
- the command palette, before you type
- **Go to your Odoo Apps** on the website, for signed-in users

**The order follows each user's own language setting**, so two users on one database can see
different orders. Case is ignored and accented names are sorted correctly, so *Ángulo* sorts beside *Anzuelo*.

**Limits**

- **The menus inside each app keep their own defined order.** Only the list of apps is sorted.
- **On Enterprise, a user who has rearranged their apps grid keeps their own arrangement.**
- **The command palette ranks by relevance once you type**, as in standard Odoo.
- **Spanish ñ is sorted as n.**

**Changelog**

*18.0.1.0.2 (1 October 2026)*

- Browser tests added. No change in behaviour.

*18.0.1.0.1 (30 September 2026)*

- Fewer database queries on every backend page load: the pinned menus are found without
  reading their records. No change in behaviour.

*18.0.1.0.0 (28 September 2026)*

- First release for Odoo 18, ported from 19.0.1.1.1. No change in behaviour.
