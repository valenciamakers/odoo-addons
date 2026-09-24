Switch your own backend language from a systray dropdown.

In standard Odoo, changing your backend language means opening your preferences, finding the
language field, and saving. This module adds a globe to the top bar: click it, pick a language, and
the backend reloads in it.

**Installation**

Install **Backend Language Menu** from the Apps menu. It only requires Odoo's **web** module, and works on both Community and Enterprise.

**Using it**

There is nothing to configure. The globe appears in the top bar, beside the company switcher, as
soon as more than one language is enabled.

- **Click the globe** to see every enabled language, with a check beside your current one.
- **Pick a language** to switch to it. Only your own backend language changes; other users and the
  website are unaffected.

Every internal user can use it, with no extra access rights. With **Language Sequence** installed,
the menu lists languages in the order you set.

**To show the language name** beside the globe, turn on developer mode, go to **Settings >
Technical > System Parameters**, and add *vmk_language_systray.show_name* with the value *True*. It
applies to every user, on wide screens.

**Limits**

- **The menu hides on phone-width screens**, as the company switcher does. Use your preferences
  there.

**Changelog**

*19.0.1.1.1 (24 September 2026)*

- Licensed LGPL-3, and credited to Valencia Makers. No change in behaviour.

*19.0.1.1.0 (19 August 2026)*

- Licensed AGPL-3, from MIT. No change in behaviour.

*19.0.1.0.0 (15 August 2026)*

- First release. A globe in the backend's top bar switches the current user's language.
