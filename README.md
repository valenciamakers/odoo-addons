# Odoo Addons

Odoo 19 modules written and maintained by Valencia Makers, SL — a digital-fabrication education,
makerspace, and retail business in Valencia, Spain. Each one is small, solves a problem we hit
running our own instance, and is copyleft-licensed — AGPL-3, or LGPL-3 where the module is meant to
be built on.

They depend only on Odoo Community modules, so they work on Community and Enterprise alike.

## Modules

- **[`vmk_language_sequence`](vmk_language_sequence)** — order the enabled languages by hand, by
  dragging, instead of alphabetically: in the website language selector, the language dropdowns on
  users and contacts, and the Languages list itself.
- **[`vmk_language_freeze_meta`](vmk_language_freeze_meta)** — stop Odoo module updates reverting
  your edits to language records, such as a renamed language or a broadened ISO code.
- **[`vmk_apps_menu_sort`](vmk_apps_menu_sort)** — sort the apps on the main menu alphabetically
  rather than by the `sequence` each module picked for itself, keeping Apps and Settings at the end.
- **[`vmk_apps_page_sort`](vmk_apps_page_sort)** — sort the Apps page by the name on the card, since
  `ir.module.module` orders by the technical name it does not display.
- **[`vmk_settings_sort`](vmk_settings_sort)** — sort the Settings sidebar and the Technical menu's
  groupings alphabetically, with General Settings kept at the top.
- **[`vmk_partner_email_multiple`](vmk_partner_email_multiple)** — several email addresses per
  contact, so mail from any of them is matched to the contact you already have instead of creating a
  duplicate. Merging two contacts keeps both their addresses.

Each module's own `README.md` explains why it is built the way it is — which core method fights you,
and where. That is usually the interesting part.

## Installing

Clone onto your Odoo addons path, update the apps list, and install by name:

```bash
git clone https://github.com/valenciamakers/odoo-addons.git
odoo --addons-path=/path/to/odoo-addons,... -d <db> -i vmk_language_sequence
```

## Developing

`dev/` holds a Docker harness — Odoo 19 and PostgreSQL 17, with this repo mounted as an addons path:

```bash
cd dev
docker compose up -d db
docker compose run --rm odoo odoo -d test --init vmk_language_sequence --stop-after-init
docker compose run --rm odoo odoo -d test -u vmk_language_sequence \
    --test-enable --test-tags /vmk_language_sequence --stop-after-init
docker compose down
```

`CLAUDE.md` documents the harness's sharp edges, plus a catalogue of Odoo 19 behaviours that cost us
time — all verified against real Odoo source rather than against documentation.

## Contributing

Issues and pull requests are welcome. These are maintained for our own use first, so a change that
suits your deployment but not ours may be happier as a fork, and no hard feelings — the licences
here are chosen to keep forking open, not to close it.

We have no CLA, which means we cannot relicense contributed code. Bear that in mind if you send
something substantial.

## License

© 2026 Valencia Makers, SL. Licensed per module — see each module's `LICENSE` and manifest:

- **AGPL-3** for everything by default. Use them freely, including commercially; distribute a
  modified version and it stays AGPL, with source.
- **LGPL-3** for `vmk_partner_email_multiple`, so other modules may depend on it under any licence.
  Its README explains why it is the exception.
