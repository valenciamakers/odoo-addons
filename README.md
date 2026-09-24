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
- **[`vmk_event_host`](vmk_event_host)** — record who runs an event: the speakers, teachers or
  facilitators, as contacts. An event can have several, and they are searchable and groupable.
- **[`vmk_event_slot_multiday`](vmk_event_slot_multiday)** — let an event slot end on a later day
  than it starts, such as Friday evening to Sunday afternoon. Everything that reads the slot's end
  follows: the calendar, the attendee's registration, and scheduled mail.

Each module's own `README.md` explains why it is built the way it is — which core method fights you,
and where. That is usually the interesting part.

## Installing

Clone onto your Odoo addons path, update the apps list, and install by name:

```bash
git clone https://github.com/valenciamakers/odoo-addons.git
odoo --addons-path=/path/to/odoo-addons,... -d <db> -i vmk_language_sequence
```

## Developing

Valencia Makers maintains a shared dev harness at `../Tech Stack/odoo-dev` (private; it mounts Odoo
Enterprise, which we cannot redistribute). It mounts all three of our module repos at once in
production's addons order, keeps its databases across a restart, and can restore a neutered copy of
production data.

Working from a clone of this repo alone, the equivalent is a two-service Compose file — Postgres 17
and `odoo:19` with the repo root mounted at `/mnt/extra-addons`:

```bash
docker compose up -d db

# create a database and install a module (post_init_hook runs on install only)
docker compose run --rm odoo odoo -d test --init vmk_language_sequence --without-demo=all --stop-after-init

# run that module's tests
docker compose run --rm odoo odoo -d test -u vmk_language_sequence --test-enable --test-tags /vmk_language_sequence --stop-after-init

# serve on localhost:8069
docker compose up -d odoo
```

`.claude/CLAUDE.md` documents the harness's sharp edges, plus a catalogue of Odoo 19 behaviours that
cost us time — all verified against real Odoo source rather than against documentation.

## Contributing

Issues and pull requests are welcome. These addons are maintained for our own use first, so a change
that suits your deployment but not ours may be happier as a fork, and no hard feelings — the
licences here are chosen to keep forking open, not to close it.

We have no CLA, which means we cannot relicense contributed code. Bear that in mind if you send
something substantial.

## License

© 2026 Valencia Makers, SL. Licensed per module — see each module's `LICENSE` and manifest:

- **AGPL-3** for everything by default. Use them freely, including commercially; distribute a
  modified version and it stays AGPL, with source.
- **LGPL-3** for `vmk_partner_email_multiple`, `vmk_event_host`, and `vmk_event_slot_multiday`, so
  other modules may depend on them under any licence. Each README explains why it is an exception.
