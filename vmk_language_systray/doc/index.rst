Switch your own backend language from a dropdown in the menu bar.

In standard Odoo, changing your backend language requires opening your preferences, finding the
language field, and saving. This module adds a globe to the backend menu bar: click it, pick a
language, and the backend reloads in your new language.

**Installation**

Install **Backend Language Menu** from the Apps menu. It only requires Odoo's **web** module, and works on both Community and Enterprise.

**Using it**

There is nothing to configure. The globe appears in the menu bar, beside the company switcher, as
soon as more than one language is enabled.

- **Click the globe** to see every enabled language, with your active language clearly marked.
- **Click a language** to switch to it. Only your own backend language changes; other users and the
  website are unaffected.

Every backend user can use it, with no extra access rights required. With `Language Sequence
<https://apps.odoo.com/apps/modules/20.0/vmk_language_sequence>`_ installed, the menu follows your
custom order.

**To display the language name** beside the globe in the menu bar, enable developer mode, go to
**Settings > Technical > System Parameters**, and add *vmk_language_systray.show_name* with the
value *True*. It applies to every user, and only appears on wide screens.

**Limits**

- **The menu hides on phone-width screens**, just like the company switcher does. Switch languages
  with the normal method using your preferences.

**Changelog**

*20.0.1.1.0 (5 October 2026)*

- Translated into nineteen more languages: Chinese (Simplified and Traditional), Czech, Danish,
  Dutch, French, German, Indonesian, Italian, Japanese, Korean, Polish, Portuguese (Brazil and
  Portugal), Romanian, Russian, Swedish, Turkish, and Ukrainian.

*20.0.1.0.0 (30 September 2026)*

- First release for Odoo 20, ported from 19.0.1.1.1. The globe is now one of Odoo 20's own icons,
  since the backend no longer loads the one this module used, and is the same size as the icons
  beside it.

*19.0.1.1.1 (24 September 2026)*

- Licensed LGPL-3, and credited to Valencia Makers. No change in behaviour.

*19.0.1.1.0 (19 August 2026)*

- Licensed AGPL-3, from MIT. No change in behaviour.

*19.0.1.0.0 (15 August 2026)*

- First release. A globe in the backend's top bar switches the current user's language.
