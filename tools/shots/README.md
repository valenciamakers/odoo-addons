# Store screenshots

How the images on each module's Apps Store page are made, so any of them can be retaken. Covers are
rendered separately, by `tools/make_cover.py`, from these screenshots.

Everything here changes the page in the browser for the capture only; no module ships any of it.
That polish, in `shots.py`, hides the unread-messages counter, paints Odoo's Violet slot colour and
the signed-in user's avatar in our purple, and draws a cursor where a recipe needs one. Recipes add
their own capture-only CSS, such as hiding another module's field.

## What the recipes need

**A local Odoo with these modules installed**, from `../Tech Stack/odoo-dev`, serving the scratch
database the demo data lives in (`./odev db use shots && ./odev up`).

**A Chrome started with remote debugging, logged in to it.** Backend captures reuse one tab in that
Chrome, named by `window.name`, rather than opening a new tab each time; public-page captures run
headless and logged out.

```bash
open -na "Google Chrome" --args --remote-debugging-port=9222 --user-data-dir="$HOME/.chrome-devtools-profile"
```

The tools connect to `127.0.0.1:9222`, so only one Chrome may hold that port: a second one started
with the flag binds only the IPv6 half and is never reached. If a capture hangs or the backend tab
shows Odoo's "Offline" page, quit every Chrome and start this one again.

**The demo data**, in English (UK), which gives 24-hour times and day-first dates:

- the admin user named **Mitchell Admin**, as in Odoo's own demo data, with English (UK) as their
  language and the website's default;
- **Beginner's Bootcamp**, with Multiple Slots, three slots in Violet (the first from Friday evening
  to Sunday afternoon), a venue, and hosts **Marc Demo** (Lead Instructor) and **Edith Sanchez**
  (Assistant);
- three more events with hosts, for the grouped list: **Weekend Festival**, **Design Workshop**, and
  **Back to Basics**, the last with its own 02:00 registration deadline and an Admission ticket;
- the Registration Deadline setting on, at 01:30;
- for the deadline's public page, a published event named **Open Studio Evening** starting within
  the deadline. It is temporary by nature; recreate it just before capturing:

```python
# ./odev shell
from datetime import datetime, timedelta
start = (datetime.now() + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
env['event.event'].create({'name': 'Open Studio Evening', 'date_begin': start,
    'date_end': start + timedelta(hours=3), 'date_tz': 'Europe/Madrid', 'website_published': True,
    'description': '<p>A drop-in evening in the studio: bring a project, use the printers, and get help from the team.</p>',
    'event_ticket_ids': [(0, 0, {'name': 'Admission'})]})
env.cr.commit()
```

- for the sort modules, a spread of Odoo's own apps: CRM, Sales, Invoicing, Inventory, Purchase,
  Project, Employees, Time Off, Calendar, Contacts, Manufacturing, Point of Sale, and Helpdesk, with
  the company's country set to Spain.
- for the language modules, six enabled languages, all on the website: English (UK), English (US),
  Catalan, French, German, and Spanish. The Language Sequence recipe sets their order; the Protect
  Language Edits recipe changes Catalan's ISO code to `ca`, which protects it.
- for Multiple Contact Emails, with the module and CRM installed, a contact named **Rosa Vidal**
  with two additional addresses, and a lead that arrived by email from one of them. The lead goes
  through the mail gateway, so its contact is found the way real mail finds it; the snippet
  recreates both, so it is safe to run again:

```python
# ./odev shell
Partner = env["res.partner"]
rosa = Partner.search([("name", "=", "Rosa Vidal")], limit=1) or Partner.create({"name": "Rosa Vidal"})
rosa.write({"email": "rosa.vidal@example.com", "phone": "+34 600 123 456", "function": "Product Designer",
    "lang": "en_GB", "city": "Valencia", "country_id": env.ref("base.es").id,
    "vmk_email_ids": [(5, 0, 0),
        (0, 0, {"email": "rosa@example.org", "label": "Personal", "sequence": 10}),
        (0, 0, {"email": "rosa.billing@example.com", "label": "Billing", "sequence": 20})]})
env["crm.lead"].search([("name", "=", "Laser cutting for a small order")]).unlink()
lead = env["crm.lead"].browse(env["mail.thread"].message_process("crm.lead", """From: Rosa Vidal <rosa@example.org>
To: info@example.com
Subject: Laser cutting for a small order
Message-ID: <rosa-laser-order@example.org>
Date: Thu, 24 Sep 2026 17:42:00 +0200
Content-Type: text/html; charset=utf-8

<p>Hi, could you cut 40 coasters in 3mm birch plywood from the attached design?</p><p>Thanks,<br>Rosa</p>
"""))
tag = env["crm.tag"].search([("name", "=", "Laser Cutting")], limit=1) or env["crm.tag"].create({"name": "Laser Cutting"})
lead.write({"expected_revenue": 240, "probability": 40, "user_id": env.ref("base.user_admin").id,
    "date_deadline": "2026-10-16", "priority": "1", "tag_ids": [(6, 0, tag.ids)]})
assert rosa.email == "rosa.vidal@example.com" and lead.partner_id == rosa
env.registry.signal_changes(); env.cr.commit()
```

Recipes find records by these names, so ids do not matter. The three sort recipes uninstall their
module over RPC for the "before" captures and install it again for the "after"; `_sorting.py` waits
for the backend to come back after each, since a request made mid-reload fails.

## Running

```bash
uv run tools/make_icon.py --install-browser                      # once, if Playwright's Chromium is missing
uv run tools/shots/recipes/vmk_event_host.py                     # writes into the module
uv run tools/shots/recipes/vmk_event_host.py --out /tmp/trial    # a trial run, to compare first
uv run tools/make_cover.py vmk_event_host                        # then re-render the cover
```

Each recipe's docstring lists what it writes. Run against the current demo data they reproduce the
published images, to within a pixel of cropping.

Two checks before pushing a page:

```bash
uv run tools/shots/store_preview.py vmk_event_host /tmp/store.png   # as the Apps Store will show it
uv run tools/shots/dark_check.py vmk_event_host /tmp/dark.png dark  # in Enterprise's dark mode
uv run tools/shots/dark_check.py vmk_event_host /tmp/light.png light
```

`store_preview.py` renders the page inside the live store with the inline styles the store drops
already dropped. `dark_check.py` switches the reused tab's colour scheme, so run it with `light`
afterwards to put the tab back.
