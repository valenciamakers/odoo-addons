Stop Odoo updates from reverting your edits to language settings.

In standard Odoo, every module update resets the language settings to the default Odoo values, so a renamed
language or a changed date format is quietly overwritten. This module keeps your changes: any
language you edit will be protected from updates.

**Installation**

Install **Protect Language Edits** from the Apps menu. It only requires Odoo's **base** module, and
works on both Community and Enterprise.

**Using it**

There is nothing to configure.

- **On install**, every enabled language is protected, so edits you made before installing it are
  kept.
- **When you edit a language**, by changing its name, codes, direction, separators, date or time
  format, first day of the week, or flag, it will be protected automatically.
- **The Protect From Updates switch** on the language form shows the status. Switch it off to
  disable protection and start receiving Odoo updates again.

Enabling, disabling, or reordering a language does not protect it. Translations still update as
usual; only the language settings are protected.

**Limits**

- **Protection covers the whole language**, not individual fields, so a protected language will no
  longer receive any corrections to its settings; disable protection to receive updates again.
- **Disabled languages, and languages you enable but don't edit**, keep receiving regular Odoo
  updates.

**Changelog**

*19.0.1.1.2 (25 September 2026)*

- Renamed from *vmk_language_freeze_meta* to *vmk_language_protect_settings*. No change in
  behaviour. To move an existing database, install the new module, then uninstall the old one;
  protected languages stay protected.

*19.0.1.1.1 (24 September 2026)*

- Licensed LGPL-3, and credited to Valencia Makers. No change in behaviour.

*19.0.1.1.0 (19 August 2026)*

- Licensed AGPL-3, from MIT. No change in behaviour.

*19.0.1.0.0 (13 August 2026)*

- First release. Enabled languages are protected on install, and a language is protected when you
  edit it, with a switch on the language form.
