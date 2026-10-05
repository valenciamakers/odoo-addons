Reorder languages manually instead of alphabetically.

In standard Odoo, languages are always listed alphabetically by their English name, so a Valencia
business that offers *Català, English, Français, Deutsch,* and *Español* will display them in that
order. This module lets you drag enabled languages into any order you choose.

**Installation**

Install **Language Sequence** from the Apps menu. It works with or without the **Website** app, on both Community and Enterprise.

**Using it**

#. Turn on developer mode, then go to **Settings > Translations > Languages**.
#. Drag the enabled languages into any order, using the handle at the start of each row.

Your order is used by:

- the website language selector and the footer language list
- the language dropdowns on user and contact forms
- the pop-up for translating a field, after your own language, which Odoo always lists first
- the Languages list itself

With two variants of one language enabled, such as English (UK) and English (US), search
engines are told to use the first language in your custom order as the generic version.

New languages you enable are added to the end of the list, and can be dragged into place.

**Limits**

- **Odoo shows the Languages list only in developer mode**, and this module leaves that as it is.

**Languages**

Catalan, Chinese (Simplified and Traditional), Czech, Danish, Dutch, English, French, German,
Indonesian, Italian, Japanese, Korean, Polish, Portuguese (Brazil and Portugal), Romanian,
Russian, Spanish, Swedish, Turkish, and Ukrainian. If any translation seems incorrect, please
`contact us <mailto:info@valenciamakers.es>`_ and we will fix it.

**Changelog**

*20.0.1.3.0 (5 October 2026)*

- Translated into nineteen more languages: Chinese (Simplified and Traditional), Czech, Danish,
  Dutch, French, German, Indonesian, Italian, Japanese, Korean, Polish, Portuguese (Brazil and
  Portugal), Romanian, Russian, Swedish, Turkish, and Ukrainian.

*20.0.1.2.0 (3 October 2026)*

- The pop-up for translating a field lists the languages in your order, after your own language.
  The Point of Sale self-order kiosk still lists them alphabetically.

*20.0.1.1.0 (3 October 2026)*

- The **Website** app is no longer required, and is no longer installed along with this module.
  Where it is installed, its language selector follows your order as before.

*20.0.1.0.0 (30 September 2026)*

- First release for Odoo 20, ported from 19.0.1.2.0. The order now also reaches Odoo 20's own
  language lists, which it builds differently: the dropdowns, the portal selector, and the website
  selector all follow it, and a drag shows at once.
- The translation dialog and the Point of Sale self-order kiosk still list languages
  alphabetically.

*19.0.1.2.0 (25 September 2026)*

- With two variants of one language enabled, search engines are told to use the first language in
  your custom order as the generic version, rather than the first alphabetically. Latin American
  Spanish stays the generic Spanish whenever it is enabled, as it does in standard Odoo.

*19.0.1.1.1 (24 September 2026)*

- Licensed LGPL-3, and credited to Valencia Makers. No change in behaviour.

*19.0.1.1.0 (19 August 2026)*

- Licensed AGPL-3, from MIT. No change in behaviour.

*19.0.1.0.0 (13 August 2026)*

- First release. Enabled languages can be ordered by hand, and the website selector and language
  dropdowns follow that order.
