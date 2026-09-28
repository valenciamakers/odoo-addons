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

*18.0.1.0.0 (28 September 2026)*

- First release for Odoo 18, ported from *19.0.1.1.2*. Also protects the **Short Time Format**
  field, which Odoo 18 carries and 19 does not.
