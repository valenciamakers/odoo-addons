# Store screenshots

How the images on each module's Apps Store page are made, so any of them can be retaken. Covers are
rendered separately, by `tools/make_cover.py`, from these screenshots.

Everything here changes the page in the browser for the capture only; no module ships any of it.
That polish, in `shots.py`, hides the unread-messages counter and any onboarding tour's pointer,
paints Odoo's Violet slot colour and the signed-in user's avatar in our purple, and draws a cursor
where a recipe needs one. Recipes add their own capture-only CSS, such as hiding another module's
field.

**The tools serve the Private repo's modules too.** `tools/repos.py` finds a module, and its icon,
cover, and recipe sources, in this repo or in `../Odoo Addons - Private`, whose `tools/` keeps the
same layout. Those sources stay there because they describe modules we do not publish; a Private
recipe imports `shots.py` from here.

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

**The demo data**, in English (UK), which gives 24-hour times and day-first dates, is created by
`demo/seed.py`, idempotently — safe to re-run, finding each record by name rather than duplicating
it:

```bash
DB=shots ../Tech\ Stack/odoo-dev/odev shell < tools/shots/demo/seed.py   # from the repo root; SERIES=18.0 for 18
```

It works on both Odoo 18 and 19, branching on `odoo.release.series` where they differ — see the
script's own docstring. Odoo 18 has no `event.slot` model and neither series' harness loads demo
data (`without_demo`/`with_demo` off), so on 18 the script also creates Marc Demo and Edith Sanchez
itself, with the same avatars Odoo's own demo data uses, and Beginner's Bootcamp becomes one
ordinary event rather than a multi-slot one. What it makes:

- the admin user named **Mitchell Admin**, as in Odoo's own demo data, with English (UK) as their
  language and the website's default;
- **Beginner's Bootcamp**, with Multiple Slots, three slots in Violet (the first from Friday evening
  to Sunday afternoon), a venue, and hosts **Marc Demo** (Lead Instructor) and **Edith Sanchez**
  (Assistant). **On Odoo 18**, which has no `event.slot` model, it is instead one ordinary event
  dated a Friday evening to Sunday afternoon;
- three more events with hosts, for the grouped list: **Weekend Festival**, **Design Workshop**, and
  **Back to Basics**, the last with its own 02:00 registration deadline and an Admission ticket;
- the Registration Deadline setting on, at 01:30;
- for the deadline's public page, a published event named **Open Studio Evening** starting within
  the deadline. It is temporary by nature, so `seed.py` does not create it: call its
  `open_studio_evening(env)` on its own, right before capturing —

```bash
(cat tools/shots/demo/seed.py; echo "open_studio_evening(env)") | \
    DB=shots ../Tech\ Stack/odoo-dev/odev shell
```

- for the sort modules, a spread of Odoo's own apps: CRM, Sales, Invoicing, Inventory, Purchase,
  Project, Employees, Time Off, Calendar, Contacts, Manufacturing, Point of Sale, and Helpdesk, with
  the company's country set to Spain. `seed.py` does not install these — see "Running" below.
- for the language modules, six enabled languages, all on the website: English (UK), English (US),
  Catalan, French, German, and Spanish. The Language Sequence recipe sets their order; the Protect
  Language Edits recipe changes Catalan's ISO code to `ca`, which protects it.
- for Multiple Contact Emails, with the module and CRM installed, a contact named **Rosa Vidal**
  with two additional addresses and, as the contact's image, Lucide's `square-user-round` in our
  purple (`demo/rosa_vidal.png`), and a lead that arrived by email from one of them. The lead goes
  through the mail gateway, so its contact is found the way real mail finds it; `seed.py` recreates
  the lead on every run, so it stays matched to Rosa even after an unrelated re-seed.

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

For another Odoo series, point the tools at that stack and run them from its checkout — for 18,
`ODOO_URL=http://localhost:8169`, from `Odoo Addons - Custom (18.0)` — so a recipe writes into the
18.0 worktree and finds the private repo's 18.0 worktree beside it. Navigation waits for the page to
load and then up to five seconds of network quiet (`shots.goto`), since Odoo 18's backend never goes
quiet at all.

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
