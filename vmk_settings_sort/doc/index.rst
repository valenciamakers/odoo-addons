Alphabetical order for the Settings sidebar and Technical menu groups.

In standard Odoo, the Settings sidebar and the groups in the Technical menu appear in whatever order
their modules happen to add them. This module sorts both lists alphabetically, while keeping
**General Settings** at the top.

**Installation**

Install **Settings Sort** from the Apps menu. It only requires Odoo's **base** module, so it works
with any set of apps, on both Community and Enterprise.

**Using it**

There is nothing to configure. Once installed:

- **The settings page sidebar** is sorted alphabetically, while keeping **General Settings** at
  the top.
- **The Technical menu groups** (Actions, Activities, Automation, and the rest) are
  alphabetical. The items inside each group keep their order. The Technical menu is visible
  while the site is in developer mode.

**Both lists follow each user's own language setting.** Nothing is stored; uninstall the module and
the original orders return.

**Limits**

- **Only the order of the sidebar sections and the Technical groups changes.** Every setting and
  menu item stays where it was.

**Languages**

Catalan, Chinese (Simplified and Traditional), Czech, Danish, Dutch, English, French, German,
Indonesian, Italian, Japanese, Korean, Polish, Portuguese (Brazil and Portugal), Romanian,
Russian, Spanish, Swedish, Turkish, and Ukrainian. If any translation seems incorrect, please
contact us and we will fix it.

**Changelog**

*18.0.1.1.0 (5 October 2026)*

- Translated into nineteen more languages: Chinese (Simplified and Traditional), Czech, Danish,
  Dutch, French, German, Indonesian, Italian, Japanese, Korean, Polish, Portuguese (Brazil and
  Portugal), Romanian, Russian, Swedish, Turkish, and Ukrainian.

*18.0.1.0.2 (1 October 2026)*

- Browser tests added. No change in behaviour.

*18.0.1.0.1 (30 September 2026)*

- Fewer database queries on every backend page load: the Technical menu is found without
  reading its record. No change in behaviour.

*18.0.1.0.0 (28 September 2026)*

- First release for Odoo 18, ported from 19.0.1.1.1.
