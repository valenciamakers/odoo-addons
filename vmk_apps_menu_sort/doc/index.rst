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

**Languages**

Catalan, Chinese (Simplified and Traditional), Czech, Danish, Dutch, English, French, German,
Indonesian, Italian, Japanese, Korean, Polish, Portuguese (Brazil and Portugal), Romanian,
Russian, Spanish, Swedish, Turkish, and Ukrainian. If any translation seems incorrect, please
`contact us <mailto:info@valenciamakers.es>`_ and we will fix it.

**Changelog**

*19.0.1.2.0 (5 October 2026)*

- Translated into nineteen more languages: Chinese (Simplified and Traditional), Czech, Danish,
  Dutch, French, German, Indonesian, Italian, Japanese, Korean, Polish, Portuguese (Brazil and
  Portugal), Romanian, Russian, Swedish, Turkish, and Ukrainian.

*19.0.1.1.3 (1 October 2026)*

- Browser tests added. No change in behaviour.

*19.0.1.1.2 (30 September 2026)*

- Fewer database queries on every backend page load: the pinned menus are found without
  reading their records. No change in behaviour.

*19.0.1.1.1 (24 September 2026)*

- Licensed LGPL-3, and credited to Valencia Makers. No change in behaviour.

*19.0.1.1.0 (19 August 2026)*

- Licensed AGPL-3, from MIT. No change in behaviour.

*19.0.1.0.0 (13 August 2026)*

- First release. The apps grid, the navbar apps menu, the command palette, and the website's
  apps menu list apps alphabetically, with Apps and Settings at the end.
