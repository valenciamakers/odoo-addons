Reorder languages manually instead of alphabetically.

In standard Odoo, languages are always listed alphabetically by their English name, so a Valencia
business that offers *Català, English, Français, Deutsch,* and *Español* will display them in that
order. This module lets you drag enabled languages into any order you choose.

**Installation**

Install **Language Sequence** from the Apps menu. It requires the **Website** app, and works on both Community and Enterprise.

**Using it**

#. Turn on developer mode, then go to **Settings > Translations > Languages**.
#. Drag the enabled languages into any order, using the handle at the start of each row.

Your order is used by:

- the website language selector and the footer language list
- the language dropdowns on user and contact forms
- the Languages list itself

New languages you enable are added to the end of the list, and can be dragged into place.

**Limits**

- **Odoo shows the Languages list only in developer mode**, and this module leaves that as it is.
- **With two variants of one language enabled** (Spanish from Spain and Latin America, say), the
  website's short language code goes to the alphabetically first, whatever your order.

**Changelog**

*19.0.1.1.1 (24 September 2026)*

- Licensed LGPL-3, and credited to Valencia Makers. No change in behaviour.

*19.0.1.1.0 (19 August 2026)*

- Licensed AGPL-3, from MIT. No change in behaviour.

*19.0.1.0.0 (13 August 2026)*

- First release. Enabled languages can be ordered by hand, and the website selector and language
  dropdowns follow that order.
