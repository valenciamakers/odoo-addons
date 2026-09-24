# CLAUDE.md — Odoo Addons

The Odoo 19 modules Valencia Makers writes and maintains, LGPL-3 licensed, as Odoo itself is. They
run against a self-hosted **Odoo 19 Enterprise** instance but depend only on Community modules. See
`../.claude/CLAUDE.md` for the business context; this file wins inside this repo.

This is one of three module repos. Modules we write and do not publish — those depending on
Enterprise, and those we may sell — live in the private `../Odoo Addons - Private`, which follows
this file's conventions and adds only what differs. Third-party modules under evaluation live in the
private `../Odoo Addons - External`, never here: this repo is publishable, so nothing enters it that
we do not own. The three remotes differ by one word — `odoo-addons`, `odoo-addons-private`,
`odoo-addons-external` — so check which one you are pushing to.

## Layout

- **`vmk_language_sequence`** — manual ordering of the enabled languages.
- **`vmk_language_freeze_meta`** — stops Odoo updates reverting edits to language metadata.
- **`vmk_language_systray`** — a systray dropdown switching the current user's backend language.
- **`vmk_apps_menu_sort`** — alphabetical ordering of the apps on the main menu.
- **`vmk_apps_page_sort`** — alphabetical ordering of the Apps page, by displayed name.
- **`vmk_settings_sort`** — alphabetical ordering of the Settings sidebar and Technical groupings.
- **`vmk_event_host`** — who runs an event, as contacts; several per event.
- **`vmk_event_registration_deadline`** — stop selling registrations when an event starts, or a set
  time before; per-event override, and the same rule applied to slots.
- **`vmk_event_slot_multiday`** — an end date on event slots, so a slot can span several days.
- **`vmk_website_event_slot_multiday`** — both days of a multi-day slot in the website's
  registration modal; `auto_install`.
- **`vmk_partner_email_multiple`** — several email addresses per contact, matched by Odoo's own
  machinery, and kept rather than dropped when contacts are merged.
- **`tools/`** — not a module. `make_icon.py` renders each module's store icon from the glyphs in
  `tools/icons/`; see _Store icons_ under the authoring conventions.
- The local test harness is `../Tech Stack/odoo-dev`, shared with our other two Odoo module repos.

Read the existing modules' `README.md` files before writing another; between them they document most
of the traps below in context.

## Branches — one per Odoo series

All three module repos follow Odoo's and the OCA's convention: **a branch per Odoo series, named for
it**, and no `main`. `19.0` holds the Odoo 19 modules and is the default branch; it replaced `main`
on 24 September 2026, with the same commits. The Apps Store reads a repository by its series
branches, and oec.sh's repository settings should name `19.0` for any repo it deploys. When Odoo 20
arrives, `20.0` starts from `19.0`, which then carries fixes for Odoo 19 installs only. Work on the
series' branch; a separate branch only when Felix asks for one.

## Commits — this repo departs from the machine-wide rule

`~/.claude/rules/git-workflow.md` says to commit as `Claude <claude@pvt.jfe.xyz>` with no
`Co-Authored-By` trailer. **That does not apply here.** This repo is published, so its history
should attribute to the maintainer in order to link properly on GitHub.

- **Author and commit as Felix.** That is already the global git identity, so a plain `git commit`
  is correct — no `-c user.name=…` overrides.
- **End every commit Claude writes with a co-author trailer**, exactly
  `Co-Authored-By: Claude <noreply@anthropic.com>`, after a blank line. This is the **one** repo
  that carries it: the history attributes to Felix, and the trailer says Claude wrote it with him.
  Still no "Generated with" line and no session link. A commit Felix writes himself gets no trailer.

Correcting this took a history rewrite. From `95edc76` on (`12a0723` since the rewrite), 49 commits
went in as Claude, or as Felix without the trailer, under an earlier version of this section that
said to add no trailers; on 24 September 2026 they were rewritten to Felix as author and committer
with the trailer, keeping their dates and messages. The earlier commits show the convention as it
had been.

Signing commits: `commit.gpgsign` is on globally and signs with Felix's SSH key through 1Password,
so commits still fail while the vault is locked, which is expected and not worth investigating.

**Only follow this commit pattern in this repo.** `../Odoo Addons - External` and every other repo
keep the project-wide convention. Everything else in `git-workflow.md` still holds here: one topic
per commit, imperative subject, a `-` bullet body explaining the why, never `git add -A`, and never
`git push` — Felix does that.

## Testing locally

Modules here install by name against a local Odoo 19 with this repo on the addons path.

Valencia Makers uses a shared harness at `../Tech Stack/odoo-dev` (private; it mounts Odoo
Enterprise, which we cannot redistribute). It mounts all three of our module repos at once in
production's addons order, keeps its databases across a restart, and can restore a neutered copy of
production data:

```bash
cd "../Tech Stack/odoo-dev"
./odev install vmk_language_sequence
./odev test vmk_language_sequence
./odev up # serve on localhost:8069
```

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

Two modules here will mislead you on Community, though. `web_enterprise` replaces both the apps grid
and the settings form with its own implementations —
`web_enterprise/static/src/webclient/home_menu/` and
`web_enterprise/static/src/webclient/settings_form_view/` — so `vmk_apps_menu_sort` and
`vmk_settings_sort` are reordering a surface Community renders differently from production. Verify
those against an Enterprise instance before believing a result. (`vmk_apps_page_sort` is safe: the
Apps list is Community's own.)

### Things that will otherwise cost you an hour each

These are properties of Odoo, not of any one harness.

- **`-u` on a module that is not installed does nothing, and says so nowhere.** The run completes,
  the log looks ordinary, and the module stays `uninstalled` — no code loads, no `.po` files load.
  It is a convincing false pass: translations appear not to work, or a fix appears not to take, when
  in fact nothing ran. Check `state` rather than trusting the log —
  `SELECT name, state FROM ir_module_module WHERE name LIKE 'vmk_%';` — and use `-i` for anything
  not yet installed. Easy to hit after recreating a database, which leaves you with only the one
  module you passed to `--init`. (`./odev upgrade` refuses outright rather than letting this
  happen.)
- **There is no `--uninstall` flag.** Use `button_immediate_uninstall()` on the `ir.module.module`
  record from a shell, with the server stopped.
- **`odoo shell` does not signal cache invalidation to the running server.** `service/model.py`
  calls `registry.signal_changes()` after each RPC; the shell has no such hook, so a write there
  leaves other workers stale. Call `env.registry.signal_changes()` **before** `env.cr.commit()`, or
  restart the server. Getting this backwards looks exactly like a caching bug in your module.
- **The running server holds the Python it started with**, unless `--dev=reload` is on and the
  watcher saw the change. Restart after editing code, or you are testing the previous version — and
  restart regardless after changing a `__manifest__.py` or an asset bundle.
- **A second database breaks the website unless the server is told which one to serve.** With two
  and no `dbfilter`, Odoo can no longer auto-select, serves the database selector instead, and
  anonymous frontend requests 404. Set `db_name` (`-d`, or `PGDATABASE`) — `http.py db_filter()`
  falls back to exposing exactly that database — or drop the spare, rather than debugging the site.
- **`docker compose down` destroys databases unless Postgres' data directory is a named volume.** It
  is easy to make only the Odoo _filestore_ a named volume, in which case `down` discards every
  database while faithfully preserving the filestore of the databases it just deleted. Use `stop` to
  pause, or make both named.
- **`docker compose exec` skips the entrypoint**, which is what translates `HOST`/`USER`/`PASSWORD`
  into CLI flags. Either pass `--db_host=db --db_user=odoo --db_password=odoo` to anything run that
  way, or put those settings in the config file at `$ODOO_RC` (`/etc/odoo/odoo.conf` in the official
  image), which Odoo reads for itself.
- **A fixture created and then modified inside one flush cycle produces no tracked change.**
  Tracking compares against the values at the last flush, so a `TransactionCase` that creates a
  record in `setUpClass` and writes to it in the test sees an empty chatter and looks like a
  tracking bug in your code. Flush between the two — `self.env.flush_all()` then `self.cr.flush()`,
  which is all `MailCommon.flush_tracking()` does.
- **`-u <module> --test-enable` runs only the tests of modules being updated.** Tag core's suite in
  (`--test-tags /event,/<ours>`) and it still does not run unless `event` itself is updated. To run
  a dependency's tests alongside ours, update the dependency, which updates everything above it:
  `DB=<scratch> ./odev test event --test-tags /event,/website_event,/<ours>`. Added 2026-09-24.
- **A changed view shows up the second time it is opened.** The web client keeps every view it loads
  in the browser's disk cache (`orm.cache({ type: "disk" })` around `get_views` in
  `web/static/src/views/view_service.js`), shows that copy at once and refreshes it in the
  background. After an upgrade, the first opening shows the old view even after a restart and a
  reload. Open it again before debugging. Added 2026-09-24.

## Deploying to production

**New files plus a restart do not upgrade anything.** Odoo creates columns only during an install or
upgrade, so a deploy has to include that step. Skipping it has taken production down twice, and a
new field on a **core** model takes the whole instance down rather than just the module, because
Odoo prefetches every stored field of a record in one `SELECT`.

oec.sh's **quick update** button does the whole deploy — git pull, upgrade, restart — and is the
normal path, since the step it performs is the one that has broken production before. Two things it
does not do: it takes **no backup** (take one first, upgrades are one-way), and it upgrades at
`-u all` scope, which re-applies every module's `data` records and so reverts anything hand-edited
in the UI that came from a module data file. Use a targeted
`odoo -u <module> --no-http --stop-after-init` when that matters.

Verify with `latest_version` and `license` on `ir_module_module` rather than a clean log — both are
written only during an install or upgrade. The full procedure, including a query that answers
whether this database has hand-edited module data at all, is in
`../Tech Stack/oec.sh/Deploying Addon Updates.md`.

## Verify against source, not memory

Read the real 19.0 source before building on any claim about what Odoo does. It is right there in
the image:

```bash
docker run --rm odoo:19 bash -c "grep -rn 'def _get_frontend(' /usr/lib/python3/dist-packages/odoo/"
docker create --name odoo19src odoo:19
docker cp odoo19src:/usr/lib/python3/dist-packages/odoo/addons/base/models/res_lang.py .
```

**The `odoo-development` plugin's skill files are stale for 19.0** — they document `<tree>`
throughout, and claim type annotations are mandatory when core does not use them. Treat them as a
starting point, never as authority.

**Read the JavaScript too.** Ordering, drag behaviour, and view composition are frequently decided
in `web/static/src/**`, not in Python. Half the surprises below live there.

## Odoo 19 traps, verified

**Views**

- `<tree>` became `<list>` in 18, but core **view record ids kept their old names** —
  `base.res_lang_tree` defines a `<list>`. Anchor an xpath on a named field
  (`<field name="x" position="before">`), never on the root tag, and it survives the rename.
- `attrs="{...}"` was removed in 17. Use direct attributes (`invisible="not active"`).
- Ship `static/description/index.html`. Without it `ir.module.module._get_desc()` falls back to
  running your `README.md` through **docutils as RST**, which spews parse errors on every install
  and renders the Apps description badly.
- `groups="base.group_no_one"` means developer mode. Several core screens are gated this way,
  including Settings → Translations → Languages.
- **A `--` inside an XML comment is a parse error** —
  `XMLSyntaxError: Double hyphen within comment`, which fails the install outright. Our prose style
  uses `--` as a dash, so this catches you in data files specifically; use a comma or rephrase.
- **The search bar's relative date ranges exclude today, by design.**
  `web/static/src/core/tree_editor/virtual_operators.js:187` maps "last 7 days" to the bounds
  `(today -7d, today)`, each rendered as `datetime.combine(<day>, time(0, 0, 0)).to_utc()` — so the
  upper bound is _this_ morning's midnight and nothing created today matches. Every "last N" entry
  ends on a completed period that way, while `today`, `month to date` and `year to date` carry
  `days = 1` on the upper bound and do include the current day. A rolling window that includes today
  needs a lower-bound-only domain, or an `any of` with `today`.
- **A saved favourite keeps its domain unevaluated, so relative filters stay rolling.**
  `search_model.js:1994` serialises with `raw: true`, and `_getDomain` ends
  `return params.raw ? domain : domain.toList(this.domainEvalContext)` — `context_today()` is stored
  as text in `ir.filters.domain` and re-evaluated on every use rather than frozen to the day it was
  saved. `ir.filters.model_id` is a **Selection** of model names despite the `_id`, so a data record
  writes the literal `res.partner`, never a `ref=`.
- **A `state="code"` server action only shows its Run button when `model_id` is `ir.actions.server`
  itself.** `view_server_action_form` carries
  `invisible="model_name != 'ir.actions.server' or state != 'code'"`, and `model_name` is
  `related='model_id.model'`. Bind a standalone action to the model its code happens to touch and it
  stays callable from `run()` — so a test calling `run()` still passes — while being unreachable
  from the interface entirely. Assert `model_name` in the test, not just that it runs.

- **A tab's x2many list only gets the full-width treatment when it is the tab's first element.**
  `form_controller.scss` ("Full width on first x2many") matches `> :first-child` of the tab pane and
  sets two custom properties on `.o_list_renderer` —
  `--ListRenderer-margin-x: var(--Notebook-margin-x)` pulls the table out to the form sheet's edges,
  and `--ListRenderer-table-padding-x: var(--Notebook-padding-x)` repads the cells so the columns
  land back on the tab's content edge. Put anything above the list — a paragraph, a row of links —
  and the list silently keeps the default 8px cell padding instead, sitting visibly inset from the
  text above it. Set those two properties yourself rather than reaching for negative margins: the
  wrapper's width is not yours to change, and the variables track whatever the sheet padding is.

- **A field a widget declares only through `fieldDependencies` never triggers an onchange, and is
  never saved.** The server marks a field `on_change` only when the view's arch contains it, so an
  edit to a widget-only field leaves every computed field on screen stale until the record is saved.
  `addFieldDependencies` (`web/static/src/model/relational_model/utils.js`) also defaults each
  dependency to `readonly: true`, which keeps it out of the save. Declare them
  `{ ..., readonly: false, onChange: true }`, as core's `project_task_kanban_model.js` does with
  `makeActiveField({ onChange: true })`. Found only on a database without a sibling module that
  happened to put the same field in the arch. Added 2026-09-24.
- **Extension views apply in priority-then-id order, so two modules' extensions of one view apply in
  whichever order they were installed.** An extension anchoring on an element another module's
  extension adds works on a fresh install and fails on a database where ours is older:
  `Element '<field name="start_datetime">' cannot be located in parent view`. Inherit from that
  module's extension (`inherit_id` its xmlid), which orders them explicitly. And where our own
  extension replaces something of core's, hide it (`invisible="1"`) rather than removing it, so
  other modules' anchors keep working. Added 2026-09-24.
- **A view built per user needs its inputs in the cache key.** Overriding `_get_view` to shape the
  arch at request time works, but the result is cached on `_get_view_cache_key`: view id, type,
  `mobile`, `env.lang`, and any `*_view_ref` context keys (`base/models/ir_ui_view.py`). Anything
  else the arch depends on goes into an override of that method, or the first user's version is
  served to everyone. `vmk_event_sessions` orders its weekday checkboxes by `res.lang.week_start`
  and adds it to the key: editing a language clears the `'stable'` cache, never the views'. Added
  2026-09-24.
- **Datetimes render in the browser's timezone, not the user's preference and not the record's.**
  Nothing in `web` sets luxon's `Settings.defaultZone`, so it is the system zone. Core's slot
  calendar shows slots in the event's timezone by converting and relabelling
  (`event_slot_calendar_model.js`, `normalizeRecord`:
  `setZone(tz).setZone("local", { keepLocalTime: true })`), and writes the slot's date and hours
  back from that wall-clock time (`buildRawRecord`). `vmk_event_slot_multiday`'s range widget does
  the same around core's own `DateTimeField`, through a proxy of the record. Added 2026-09-24.
- **The calendar view only drags a record whose start field is writable** (`calendar_model.js`,
  `canEdit`), so a computed start without an inverse makes a calendar read-only for moves. And a
  refused drag stays drawn where it was dropped: `updateRecord` does not reload on failure, so
  reload in a `catch` and rethrow. Added 2026-09-23.
- **Core's slot calendar creates slots with the datetimes in the vals as well as the date and
  hours** (`buildRawRecord` on top of the generic raw record), relying on the computed datetimes
  being ignored. Give them an inverse and every click-created slot is shifted for a viewer outside
  the event's timezone. Added 2026-09-24.
- **A server action with a `path` binds `record` only when `active_model` is its own model**, so a
  cold load of its URL runs with `record` as `None`; read `env.context.get("active_id")` instead.
  And the action service reuses parameters from session storage keyed on `active_id`, so an action
  returned without `active_id` in its context can open with the previous record's data. Put
  `active_id`, `active_ids` and `active_model` in the returned context. Added 2026-09-23.
- **`data` files load in manifest order, and a fresh install is the only test of it.** A view whose
  button references an action defined in a later file fails with "External ID not found" on a new
  database, and never on one where the action already exists. See _Test the minimal install_ below.
  Added 2026-09-23.

**Models**

- An inherit-only module needs **no `security/ir.model.access.csv`** — ACLs are per model, and
  adding a field to an existing model inherits them. Generators emit one anyway; delete it.
- `models.Constraint()` replaces `_sql_constraints`.
- **Odoo creates every database with `LC_COLLATE 'C'`** — `service/db.py` passes it whenever the
  template is `template0`, which is the normal path. So any SQL `ORDER BY` on text is byte order:
  capitals sort before lowercase (`CRM` before `Calendar`) and accented initials land after `Z`.
  Neither `_order` nor a view's `default_order` can fix it, both taking bare field names with no
  room for `lower()`. Sort in Python, or store a normalised key and order on that.
- `post_init_hook(env)` takes the environment, and runs on **install only** — never on upgrade. If a
  hook seeds data, an upgrade will not re-seed it; apply it by hand when testing on an existing
  database.
- **Deleting a module from disk leaves its `ir.module.module` row behind forever.** `update_list`
  iterates only the manifests it finds (`for manifest in modules.Manifest.all_addon_manifests()`)
  and has no branch reconciling rows whose module has gone, so "Update Apps List" never clears it.
  The orphan keeps its last-known `application` flag and so still appears as a card on the Apps
  page, offering an Install button that errors. Renaming one of our modules is the usual way to land
  here: uninstall the old name, then `unlink()` the record, which is unrestricted and takes its
  `ir.model.data` row with it. Audit a database against disk from `odoo shell`, keeping each
  statement unindented since the REPL needs a blank line to close a block:

  ```python
  from odoo.modules.module import Manifest
  on_disk = {m.name for m in Manifest.all_addon_manifests()}
  orphans = env["ir.module.module"].search([]).filtered(lambda m: m.name not in on_disk)
  print(len(orphans), "orphans:", [(o.name, o.state) for o in orphans])
  ```

  Sanity-check before deleting: core modules in that list mean the shell has a narrower addons path
  than the server, not that the database is broken. Never `unlink()` a row still reading `installed`
  — its tables and columns are live with no code behind them.

- Check a field's declared default before relying on it. `res.lang.active` is `fields.Boolean()`
  with **no default**, so a hand-created language is disabled.
- **`_rec_names_search` takes dotted paths**, not just field names on the model —
  `_search_display_name` walks each entry resolving the last field in the chain, so
  `child_ids.email` widens an autocomplete with no helper field and no `search=` method. But it is a
  plain class attribute, so _appending_ to one means restating the whole list and silently losing
  whatever core adds to it later. Where that matters, override `_search_display_name` and combine
  the domains, matching its own choice of `AND` for negative operators and `OR` otherwise.
- **The ORM checks a write's plain fields before it runs any inverse** (`write`: validate
  "non-inversed fields first", then inverses, then the rest; `create` likewise validates stored
  fields first). So an alternative input — an end date standing in for a stored day count, say —
  written together with a field a constraint reads meets that constraint before its inverse has run.
  Translate the alternative input into the stored fields in `create` and `write`, before `super()`,
  and refuse it when it disagrees with the stored field given beside it. Added 2026-09-24.
- **Defaults filled in by an override look like the caller's.** A `create` that calls
  `_add_missing_default_values` to decide something, then passes the filled-in vals to `super()`,
  hands the next override a default as if the caller had written it — which is how a default day
  count of 0 overrode an explicit end date. Use the filled-in copy for the decision, and pass the
  caller's own vals on. Added 2026-09-24.
- **A stored compute is not recomputed on upgrade.** Changing what one computes leaves every
  existing row at its old value until something it depends on changes. Released, that needs a
  `migrations/<version>/post-migrate.py`; unreleased, a one-off recompute on dev
  (`env.add_to_compute`) will do. Added 2026-09-23.
- **A compute or constraint override replaces core's by name**, since it is a method like any other.
  To relax core's rule for some records only, call it on the rest:
  `super(Model, records - exempt)._check_x()`. And guard core's compute where your view shows a
  field core's own view never did: core's `event.slot._compute_datetimes` fails on a new slot with
  no event yet, which core's form never displays and ours did. Added 2026-09-24.
- **A computed field becomes writable when it gains an inverse** — `readonly` defaults to
  `not inverse` (`fields.py`) — and redefining a core field in an `_inherit` with only `inverse=`
  merges into core's definition.
- **One2many `copy=True` on both a parent and a child relation copies the grandchildren twice.**
  Core copies `event.event.event_slot_ids`; a sessions one2many on both the event and the slot made
  each copy the same sessions, the event's still pointing at the original's slots. Copy them once,
  in the parent's `copy`, through a map of old slot to new. Added 2026-09-23.
- **A local date is not a UTC datetime's `.date()`.** An evening session west of Greenwich ends on
  the next UTC day. Use the record's own local `date` field, or convert with its timezone first.
  Added 2026-09-23.

**Mail templates**

- **Core's mail templates cannot be inherited.** Their bodies are `mail.template` records in
  `noupdate="1"` data files, not views, and the date lines of `event.event_subscription` are written
  straight into the body. Editing core's record in place is invisible to anyone reading our module
  and lost to anyone who resets the template. So `vmk_event_sessions_mail` ships **copies**, byte
  for byte except their id, name, description and five inserted lines, generated from core's file
  rather than typed. Added 2026-09-24.
- **A copy keeps core's licence**, so it lives in an LGPL-3 module of its own, and **a test holds it
  to core**: read core's file with `odoo.tools.file_open("event/data/mail_template_data.xml")`,
  strip the inserted lines, swap the id, name and description back, and compare with core's record
  exactly. An upgrade that changes the original then fails the test instead of drifting silently.
  Render both with `template._render_field("body_html", ids)` to prove a case with nothing to insert
  is core's email exactly.
- **A template body is translated as one entry**, the whole HTML body, not term by term. A copy's
  translations are core's own `msgstr` for that body with the same lines inserted.

**Module data is re-applied on every update**

- Anything Odoo ships as `data` is rewritten by `-u <that module>`, and `-u all` therefore rewrites
  nearly everything. User edits to shipped records do not survive. `base/data/res.lang.csv`
  resetting a renamed language is the case we hit.
- **A CSV data file cannot opt out.** Only XML can carry `<data noupdate="1">`, so every CSV row
  loads updatable. Freeze an individual record by setting `noupdate` on its `ir.model.data` row:
  `_load_records` skips it while updating (`if not (update and d_noupdate)`), and the xmlid upsert
  writes only `(model, res_id, write_date)`, so the flag is never cleared by the file that made it.
- Protection is per record, not per field — a frozen record stops receiving genuine Odoo corrections
  too. Freeze deliberately, and give the user a way to unfreeze.
- When overriding `write()` to react to user edits, exclude the loader: it reaches writes through
  `_load_records_write`, so mark the context there or Odoo re-applying its own data looks like a
  customisation.

**Ordering, if you add a `sequence`**

- A list view carrying `widget="handle"` and no `default_order` gets `<handle field>, id` imposed by
  the **web client** (`web/static/src/views/list/list_arch_parser.js`), overriding the model's
  `_order` entirely. Your `_order` will not order that list.
- You cannot fix that with `default_order`: `canResequenceRows` only permits dragging when
  `orderBy[0].name` **is** the handle field. Any order starting with something else silently
  disables drag and drop. Grouping therefore has to live in the sequence _values_.
- **Seed distinct values.** On tied or non-monotonic sequences, `resequence()` in
  `web/static/src/model/relational_model/utils.js` sets `reorderAll` and rewrites the entire list;
  with strictly increasing values it rewrites only the records between the two drag positions.
- Cover `create()` as well as `write()`. A record created later takes the field default and lands
  wherever that points, reintroducing ties.

**Module names**

- **The "Events" app is `website_event`**, not `event`. `website_event` carries `'name': 'Events'`
  and `application: True`, and depends on `website`; `event` is "Events Organization" and is not an
  app. So anyone who installed Events from the app grid has the website, and "requires the Events
  app" is wrong for a module depending only on `event`. "Website Events" is not a name Odoo uses at
  all. Check a module's `name` in its manifest before naming it in copy. Found 24 September 2026,
  after the multi-day store pages had shipped saying otherwise.
- **An auto-install module installs only while one of its dependencies is being installed**
  (`button_install` in `base/models/ir_module.py`: some dependency must be `to install`). One that
  arrives in the addons path after its dependencies are installed sits uninstalled until someone
  installs it.

**Caches**

- Odoo caches by **name**: `'default'`, `'stable'`, and others. `Registry.clear_cache(*names)`
  clears whole groups, and the per-method `ormcache.clear_cache()` of older versions **is gone in
  19** — there is no narrow invalidation.
- So prefer reading values from a cache that core already invalidates over clearing a broad one
  yourself. `res.lang.write()` clears `'stable'`; sorting on values from there avoided clearing
  `'default'` — every compiled QWeb template on the site — on each reorder.
- **`_order` is not the last word on ordering.** Core routinely sorts explicitly past it:
  `res.lang.get_installed()` goes through `search_fetch(..., order='name')` and
  `website._get_frontend()` uses `language_ids.sorted('name')`. Grep for the _consumers_ of an
  ordering before assuming a model-level change reaches them.
- A custom `__getitem__` can break `in`. `LangDataDict` returns a dummy for unknown keys instead of
  raising, and `Mapping.__contains__` is built on `__getitem__` — so `key in it` is **always true**.
  Build a plain `dict` when you need real membership.

**Menus, and the order of the apps**

- Root menu order is `ORDER BY sequence, id`, decided once server-side. `load_menus` calls
  `search_fetch` with no `order`, so the model's `_order` settles it, and the client preserves that
  verbatim — `menu_service.js`'s `getApps()` is a bare `.map()` over `root.children`.
- **Apps and Settings are pinned by nothing.** They carry `sequence` 500 and 550 in
  `base/views/base_menus.xml` by convention alone, and `base.menu_tests` sits above both on 1000, so
  there is no ceiling to inherit.
- **There are two app-list payloads**, cached separately. `load_menus` feeds the whole web client;
  `load_menus_root` feeds `website`'s "Go to your Odoo Apps" dropdown, rendered server-side through
  a `t-foreach` that applies no sort. Only `load_menus` entries carry an `xmlid` — `load_menus_root`
  builds its children with `read()`.
- Menu `create`/`write`/`unlink` each call a bare `registry.clear_cache()`, which covers `'default'`
  where all three menu caches live. Anything reordering menus needs no invalidation of its own.
- A bare `/odoo` lands on `res.users.action_id` if the user has one, else on `root.children[0]` —
  literally the first app (`webclient.js` `_loadDefaultApp`). Reordering root menus therefore moves
  the post-login screen on Community. Enterprise overrides that method to open the app grid instead,
  so it is unaffected.
- **Enterprise re-sorts the grid client-side** once a user drags an icon: `reorderApps` applies
  `homemenu_config`, a per-user `fields.Json` on `res.users.settings` that only Enterprise defines.
  Server-side ordering is the baseline, not the last word — and apps missing from a stored order
  sort ahead of the ones named in it, so new apps land at the front for those users.
- **`load_menus(debug)` does not use its own `debug` argument for visibility.** That argument only
  feeds the ormcache key; `_filter_visible_menus` reads `request.session.debug` instead. With no
  request there is no debug, so a `groups="base.group_no_one"` menu — the whole Technical subtree —
  is absent from any payload fetched in a `TransactionCase`, however you call it. Test that ordering
  against a fixture and verify the live path over an authenticated HTTP session.
- **The Settings sidebar is drawn in arch order.** `settings_form_compiler.js` walks
  `{selector: "app"}` in document order and `settings_page.js` sorts nothing, so the order is
  whichever order the inheriting views were applied in. General Settings leads only because
  `base_setup` sets its view's `priority` to `0`. Sort it by overriding `_get_view` on
  `res.config.settings` — after `super()`, where the arch is fully combined and no third-party xpath
  can still be broken — and remember `<form>` holds non-`<app>` children that must not move.

**Contacts, email, and matching**

- **`res.partner.mobile` no longer exists in 19.** Only `email` and `phone` remain, and
  `_phone_get_number_fields` filters candidates with `if number_fname in self`. Any module written
  for 17/18 that redefines `mobile` — most Apps Store contact modules do — is dead code at best.
- **Matching searches `email_normalized`**, a stored compute from the `mail.thread.blacklist` mixin
  using `email_normalize(record[self._primary_email], strict=False)`. `strict=False` keeps **only
  the first address** of a comma-separated list. So the multi-email field Odoo appears to tolerate
  makes none of the later addresses matchable, while `_compute_email_formatted` renders the whole
  list as `"Name" <a@x.com,b@y.com>` — a form its own docstring calls invalid.
- **Widening that search is not enough.** `res.partner._find_or_create_from_emails` searches
  `[('email_normalized', 'in', [...])]`, then resolves each input back to a partner by comparing
  `partner.email_normalized == email_normalized`. Satisfy the domain through a related table and the
  resolution step still returns an empty recordset — override **both** halves.
  `mail.thread._mail_find_partner_from_emails` repeats the same filter independently, and the legacy
  `find_or_create` searches separately again. Bounce handling and loop detection bypass all three
  with raw domains on `email_normalized`.
- **Only the resolution half of `_mail_find_partner_from_emails` is its own.** Its search delegates
  through `_partner_find_from_emails` to `res.partner._find_or_create_from_emails`, so widening that
  one method covers the mail gateway, author resolution, and recipient resolution together. What it
  then does alone is re-resolve by `p.email_normalized == email_key or p.email == email_key`, which
  drops the very partner the delegation just found.
- **The merge wizard re-points foreign keys in raw SQL, and deletes on conflict.**
  `_update_foreign_keys` (`base/wizard/base_partner_merge.py`) finds every FK to `res_partner` from
  the schema, so a child table's rows follow the surviving contact for free. But where the table
  carries a unique or check constraint, the `UPDATE` runs in a savepoint and any `psycopg2.Error`
  falls back to `DELETE FROM <table> WHERE <column> IN <all source ids>` — **one collision destroys
  every source row in that table**, not just the conflicting one. Keep uniqueness in Python with
  `@api.constrains`, which the raw SQL bypasses anyway. `_has_check_or_unique_constraint` asks
  whether a constraint touches **the foreign key column being re-pointed**, so the obvious
  `unique(partner_id, <something>)` is precisely the one that arms this; a constraint naming neither
  the FK column nor anything else it updates is invisible to the check and blows the transaction up
  instead.
- `_update_values` in the same wizard skips o2m/m2m and computed fields, and for plain fields takes
  the last truthy value with the destination last — so the destination wins and the merged-away
  values are simply dropped. It also refuses outright when contacts differ by email, except for
  admins, who are exempted two lines earlier.
- **The blacklist is narrower than it looks.** `mail.blacklist` keys on a normalized address string
  globally, and only mass mailing and SMS consult it — `mail/models/mail_mail.py` never does, so
  transactional mail goes out regardless. Addresses land there by unsubscribe or by auto-blacklist
  after repeated hard bounces.

## Authoring conventions

**Be a first-class citizen: mimic core, reuse core, and never overwrite it.** Felix, 21 September
2026: _"we mimic (and reuse from) core as much as possible. We want to be a first-class citizen, and
care to not overwrite terms, concepts, behaviors."_ An addon that invents its own vocabulary or
quietly rewrites shared state reads as foreign to anyone who knows Odoo, and breaks in ways nobody
can attribute to it.

In practice that is four different things, and only one of them saves work:

- **Reuse the component, not the wording.** Where core ships a widget, a view or a field that does
  the job, use it: those strings then belong to core and never enter our catalogue at all. Copying
  core's _wording_ into our own field is worth doing for the reader, but it costs exactly the same
  to translate — a related field carries core's English and still needs our own `.po` entry.
- **Never assert a translation for a record we do not own.** Every module that `_inherit`s a model
  gets its own `ir.model.data` xmlid pointing at the _same_ row, so the exporter writes core's model
  descriptions and inherited field help into our `.pot` under our namespace. Translating them makes
  our `.po` claim a value for a shared row. `_load_module_terms` defaults to `overwrite=False`, so
  the ordinary upgrade is safe — but "Update Translations" and `-l` pass `overwrite=True`, and then
  we clobber whatever core or the user put there. Leave those `msgstr` empty; the importer skips
  them.
- **Copy core's translation, not just core's English.** Where a string of ours says what core says,
  its `msgstr` is core's `msgstr` — looked up in `base/i18n/<lang>.po` or the relevant module's, and
  pasted verbatim. This is not optional polish: the ORM's automatic fields (`create_uid`,
  `create_date`, `write_uid`, `write_date`, `display_name`, `id`, `company_id`) land in our `.pot`
  as rows on _our_ models, so nothing is being overwritten and they do need filling in — but if we
  translate them ourselves, our model reads "Creado por" where the rest of the backend reads
  something else, or worse the reverse. Felix, 21 September 2026: _"you should just be copying core
  terminology when possible. Both in English, and for translations."_ Applies equally to any term we
  deliberately took from core: having matched the English, match the Spanish and the Catalan.
- **Where you depart from core anyway, declare it.** Copying core's _wording_ is the rule; copying
  its _typography_ or its outright mistakes is not, and neither is copying a translation that is
  simply wrong for our sense of the word. Two stand today: core's Catalan _User Settings_ carries a
  stray space after the apostrophe in twelve modules, and core renders a bare _Slot_ in Catalan as
  `Ranura`, a groove, where ours means a band of time. A departure goes in three places or it rots —
  the module's `README.md` with the reason and the date, a note in the `.po` header, and `DECLARED`
  in `odoo-dev`'s `check-terms.py`, which records the expected value so the exception stops covering
  the module the moment somebody edits the string. Decided 22 September 2026.
- **Extend behaviour, do not replace it.** Prefer adding to what core does over patching it out. A
  patch that stops applying raises nothing, so anything unavoidable gets named in the module's
  README with the file and line it depends on.
- **Borrow core's terms in prose.** Core says slot, venue, attendee, registration. Our internal word
  for an idea — cohort, for one — belongs in comments, never in a label, a message or a tooltip.

**Capitalise by the kind of string, following core.** Measured across every core `.pot` on
2026-09-21, so it need not be measured again:

| Kind                         | Core writes                   | Evidence                                       |
| ---------------------------- | ----------------------------- | ---------------------------------------------- |
| Field labels, column headers | **Title Case**                | 60% Title Case vs 11% sentence, 14,167 strings |
| Selection values             | **Title Case**, less strictly | 41% vs 14%, 4,268 strings                      |
| Add-line controls            | **Sentence case**             | "Add a line", "Add a section", "Add a product" |
| Dialog titles, buttons       | **Title Case**, verb-noun     | "Generate Leads", "Generate Budget"            |
| Help text, placeholders      | Sentences, full stop          | throughout                                     |

Where both spellings of one idea exist in core, Title Case wins outright: "End Date" 18 to "End
date" 3, "Start Date" 17 to "Start date" 1. The consequence is that one module legitimately carries
several capitalisations of the same words — a dialog titled _Generate Event Sessions_ whose button
says _Generate Sessions_ and whose add-line link says _Generate sessions_. That is three kinds of
string, not drift, and a translation file lining them up will make it look like drift. Say so in the
module's notes when it happens.

**Decide what the chatter says, rather than letting it happen.** Felix, 21 September 2026: _"I want
to make sure we are writing to chatter at the appropriate times. For this module and all we write."_
A module that writes to a tracked core field produces chatter entries whether or not anyone chose
them — `vmk_event_sessions` writes `event.event.date_begin`, which core tracks, so adding a session
logs a date change that never mentions the session. That is the failure mode: not silence, but a
history that records the side effect instead of the act.

So for each model a module touches, answer three things and write the answer down: whether the
record deserves `mail.thread` of its own or belongs in its parent's history; which fields are worth
`tracking=True`, remembering every one of them is a line somebody reads later; and whether a bulk
action should `message_post` once instead of leaving a dozen tracked changes. Where core already
tracks a field we write, decide whether its message is the one we want, or whether to post something
that names what actually happened.

**Name every module `vmk_<what it does>`** — Valencia Makers, not anyone's initials. Apps Store
technical names are a single global namespace, so an unprefixed generic name like
`language_sequence` is exactly the kind most likely to collide, and a collision blocks publishing.
Other publishers do the same: `kw_` is Kitworks, `muk_` is MuK IT, `ks_` is Ksolves.

**Check the name is free before settling on it.** A prefix is not a reservation — nothing stops two
publishers using `vmk_`, and only a full technical name actually collides. The Apps Store exposes
each module at a predictable URL, so a direct request is the test:

```bash
curl -s -o /dev/null -w '%{http_code}\n' https://apps.odoo.com/apps/modules/19.0/kw_mock_mail_server
curl -s -o /dev/null -w '%{http_code}\n' https://apps.odoo.com/apps/modules/19.0/vmk_your_new_module
```

**Probe a name known to exist first**, as the first line does. If the URL pattern ever changes,
every lookup returns 404 and a taken name is indistinguishable from a free one — the check would
silently always pass. `200` means taken, `404` means free.

Do not rely on the store's search box: searching `vmk` returns nothing even though prefixes clearly
exist in the catalogue, because the technical name does not appear to be an indexed field.

Two limits worth stating plainly. This is a point-in-time check, not a reservation — someone could
publish the same name between our checking it and our publishing, though with a vendor prefix that
is unlikely. And it only covers the Apps Store; a module distributed purely through GitHub would not
show up at all.

Manifest: `"version": "19.0.1.1.0"` (Odoo series first), `"author": "Valencia Makers"` — **no
comma**. `author` is a comma-separated list of authors, which is how the OCA is credited beside a
company, so the Apps Store listed "Valencia Makers, SL" as two authors, "Valencia Makers" and "SL",
each linked to a search. The legal name stays in the copyright lines. Fixed 24 September 2026. Keep
`depends` minimal and honest — depend on `website` only if you override something it defines.

**Store icons are rendered by `tools/make_icon.py`, never drawn or resized by hand.** Every module's
`static/description/icon.png` is a 256px glyph in our purple, `#531B93`, on a transparent
background, from [Lucide](https://lucide.dev/icons/) (ISC), chosen 24 September 2026 over Font
Awesome, Phosphor, Tabler, and Material Symbols. The glyph's source is `tools/icons/<module>.svg`:
either a Lucide icon as published, fetched with `--lucide <name>`, or our own composition on
Lucide's 24px grid and stroke, which is how a family of modules, such as the three sort modules, is
meant to read as one. So an icon can always be rebuilt, and restyling every module is one `--all`.

```bash
uv run tools/make_icon.py --install-browser              # once: Playwright's own Chromium
uv run tools/make_icon.py vmk_foo --lucide calendar-range
uv run tools/make_icon.py --all
```

Two things the first attempts got wrong, and the tool exists to avoid. Drawing a font glyph with
Pillow and scaling it down left the edges fuzzy and aliased, so the icon is rendered at its final
size by a browser. And colours drawn in the page came out shifted, `#531B93` as `#4C1F8D`, because a
screenshot passes through colour management; so the page draws only black on white, and Pillow
paints the exact colours through those as masks. Font Awesome 4.7 stays the right choice for the
small `fa` icons _inside_ `index.html`, since the Apps Store renders those with its own copy.

**No tile behind the glyph.** The first icons were a white glyph on a purple rounded tile;
published, the store framed that tile inside its own white icon box, and Felix asked for a
transparent background instead (24 September 2026), which is also how Odoo's own app icons are
drawn. A composition knocks a gap out of a glyph with a white shape; the renderer turns white into
transparency, so the gap shows whatever the icon sits on.

**Every module has a designed cover, `static/description/cover.png`, named first in the manifest's
`images`.** The store takes the first image as the cover: the thumbnail in search results and the
picture at the top of the module's page, filled into a 2:1 frame. A bare screenshot there looked
poor next to other vendors' designed covers (Felix, 24 September 2026), and a module without one
ranks lower in the default listing, per the vendor guidelines. Each cover is
`tools/covers/<module>.html` on the shared `tools/covers/cover.css`: purple background, the module's
name and summary on the left, cards cut from the module's own screenshots on the right, and the icon
with "Valencia Makers" at the bottom. `tools/make_cover.py` renders it at 1760x880, 2x the 880x440
layout, with Chromium forced to sRGB so the purple stays `#531B93`.

```bash
uv run tools/make_cover.py vmk_foo
uv run tools/make_cover.py --all
```

Put a non-breaking hyphen (`&#8209;`) in a hyphenated name, or the title can wrap inside it. When a
module's screenshots are too wide to crop into a card, capture the parts the cover needs separately
into `tools/covers/img/`, so the module does not ship images its page never shows.

**The store page, `static/description/index.html`, styles its text inline.** The Apps Store and the
backend's Apps page style Odoo's `oe_*` description classes differently: the store makes body text
grey 16px at weight 300, pulls the subtitle up under the title, and paints `oe_dark` sections grey,
which Odoo 19's backend never matches. So every heading and paragraph carries the backend's own
computed values inline — `vmk_event_slot_multiday`'s page is the model to copy — and no section uses
`oe_dark`. Widths are fixed to two: 700px for paragraphs and supporting screenshots, 800px for
two-column feature grids, with the main screenshot full width. Name our modules and Odoo's apps in
bold, and link a mention of another of our modules to its store page with `target="_blank"`: the
store's rules allow only `static/description`, YouTube, Teams, and `mailto:` links, but links to its
own module pages survive in live descriptions.

**The store strips any inline style it does not allow,** silently. What survives on published pages
is colour, font, margin, padding, border, `width`/`max-width`, `display`, `line-height`,
`text-align`, and `opacity`; `gap`, `flex`, `display:grid`, and `grid-template-columns` are dropped.
So lay out with Bootstrap classes, which the store's rules ask for and the backend also loads — the
feature grid is a `row` of `col-md-6` — and space things with margins, never `gap`. The first
published pages lost both: the grid fell to one column and the icons touched their text. Screenshots
are taken at 2x in English (UK), with any polish (colours, widths, a drawn cursor) injected as CSS
during capture only, never shipped.

**The manual, `doc/index.rst`, has no RST headings.** The store shows it in a Documentation tab with
headings at 53px, 42px, and 31px against 16px text, and pure RST cannot set a size; top-level
sections are always its `h2`. So there is no title (the page already names the module), section
names are bold paragraphs — **Installation**, **Using it**, **Limits**, **Changelog** — and each
changelog version is an italic line, `*19.0.1.0.1 (24 September 2026)*`, over a bullet list, newest
first. A mention of the other module where the reader should install it instead links to its store
page. Check that it parses with docutils before committing.

**Bump the version on every change to our code**, not only when a change needs an upgrade to take
effect. The manifest version is the only marker of which build someone is running, and the cost of
getting it wrong is asymmetric: a bump nobody needed is invisible, while a changed module still
claiming its old version makes every later question — did this deploy, is production current, which
build has the fix — unanswerable. `./odev doctor` reads `latest_version` straight from
`ir_module_module`, so a stale number misreports there too.

**The unit is a release, not an edit.** Iterating on a module within one working session — writing
it, reworking it, fixing what the first version got wrong — is one version, however many commits it
takes, because nothing could have been installed from any intermediate state. Bump when time has
passed and a build could have gone somewhere: deployed, published, or handed over. Felix,
2026-09-20, on a module that reached `19.0.2.4.0` before it existed anywhere but this laptop:
_"releasing a new module at 2.4.0 seems weird."_ Added 2026-09-20.

Odoo prefixes its own series, leaving three digits that we use as plain semver:

```
19.0  .  1  .  1  .  1
└──┬─┘    │    │    └── patch
Odoo      │    └─────── minor
series    └──────────── major
```

- **patch** — no behaviour change: a bug fix, a refactor, a docstring, a comment. This is the
  default, and the one to reach for whenever the change needs no upgrade to take effect.
- **minor** — new behaviour that does not break existing use: a new field, a new view, an added
  option. Usually needs `-u` to take effect.
- **major** — a breaking change: a removed or renamed field, altered data semantics, anything
  needing a migration script.

**Documentation-only changes do not bump.** A `README.md` edit is not a change to the module, and
bumping for one makes the version stop meaning anything. The test is whether a file Odoo loads
changed — Python, XML, JS, SCSS, CSV, or the manifest itself. A docstring counts, because it lives
in a file Odoo loads; a README does not.

This applies in `../Odoo Addons - Private` as well, which defers to this file.

**Every module here is LGPL-3**, the licence Odoo's own modules carry. It is an exact member of the
`Selection` on `ir.module.module`, so the manifest string is `"license": "LGPL-3"`, with the text in
a `LICENSE` file beside the manifest. Decided 24 September 2026.

**Copyleft still applies to the module itself**: a modified version of one of ours, distributed,
stays LGPL-3 with source. That is what moved us off MIT on 19 August 2026 — MIT does not merely fail
to prevent someone repackaging a module and selling it closed, it _permits_ it. What LGPL leaves
free is a module that depends on ours: it may carry any licence, proprietary included.

**Why not AGPL-3, the default from 19 August to 24 September 2026.** AGPL adds two things, and
neither was worth what it cost us:

- **The network clause**: running a modified copy as a service for others obliges sharing the
  source, where LGPL obliges it only on distribution. It is why the OCA defaults to AGPL, since
  hosting partners are exactly that case. For small utility modules the risk is low.
- **It bars proprietary modules from depending on ours.** Odoo's licence-compatibility table (in its
  [Apps FAQ](https://apps.odoo.com/apps/faq)) lets an `OPL-1` or `OEEL-1` module depend on LGPL-3
  but **not** on AGPL-3. Our own proprietary modules in `../Odoo Addons - Private` kept running into
  that — `vmk_event_host` and `vmk_event_slot_multiday` both needed an exception, since
  `vmk_event_sessions` (OPL-1) builds on them — and `vmk_partner_email_multiple` needed one because
  AGPL would push other authors to reimplement it rather than depend on it.

**And changing later only gets harder.** We are the sole copyright holder today and can relicense
freely; once outside contributors send code, with no CLA, it would need every contributor's consent.
A copy taken while a module was AGPL-3, or MIT before that, keeps the licence it was taken under.

**Say in a module's `README.md` where its licence matters**, as `vmk_event_host` and
`vmk_event_slot_multiday` do: a proprietary module depends on them, so moving them to a stricter
licence would break that.

LGPL-3 is written as additional permissions on top of GPL-3 and incorporates it by reference, so its
text alone is not a complete licence — `vmk_partner_email_multiple/LICENSE` carries both, LGPL-3
first.

Two conditions to keep true whatever the licence. **Prefer overriding to copying**: call `super()`
rather than copy-pasting a core method to tweak it, because a copy stops following core. Core is
LGPL-3 like us, so a copy is allowed licence-wise; where one is genuinely unavoidable, as with
core's mail templates, test it against core's source so an upgrade cannot leave it silently behind.
Core code that a proprietary module in `../Odoo Addons - Private` needs goes in an LGPL-3 module of
its own, as `vmk_event_sessions_mail` does. And **do not depend on an Enterprise module**: this repo
promises modules that work on Community and Enterprise alike, so one that needs Enterprise belongs
in `../Odoo Addons - Private`. That is a choice, not a licence requirement: the OEEL would allow an
Enterprise-dependent module under LGPL-3 (decided 24 September 2026).

**The MIT trap, kept because it is easy to walk back into.** Odoo validates `license` against that
fixed `Selection`, which has **no MIT entry**, and the failure is silent: module loading bypasses
the ORM, so `"license": "MIT"` installs cleanly and leaves an invalid value that renders blank in
the Apps list and raises `ValueError: Wrong value for ir.module.module.license` the moment anything
writes the field. The workaround was `"Other OSI approved licence"`. Nothing here uses MIT now, but
any licence outside that `Selection` fails the same way.

**Prettier**: a `.prettierrc` at the root covers everything, and each module carries its own as well
(`proseWrap: always`, `printWidth: 100`). Give every new module one — the duplication is deliberate,
so a module stays formatted correctly if it is ever distributed on its own.

A root config is safe _here_ precisely because everything in this repo is ours. In the private
`Odoo Addons - External` repo it would be a bug: a config opts every directory below it in,
including vendored code, and a format-on-save editor extension resolves config the same way Prettier
does while knowing nothing about our conventions. There, configs go per module and the root stays
bare.

**Ship translations from the start**, in the module's own first commit — not as a follow-up pass
once the code settles. Retrofitting them means re-reading every string you already stopped thinking
about, and a module that reaches anyone untranslated has already shipped the wrong thing.

**Translations** live in `i18n/` and are loaded automatically on install — no manifest entry. We
ship the `.pot` plus `es.po` and `ca.po`; Odoo 19 has **no Valencian variant**, so `ca_ES` is what a
Valencian speaker selects. Terms a module shares with core reuse core's own wording, taken out of
`base`/`mail`/`web`'s catalogues rather than translated afresh, so a module reads as part of the
backend instead of introducing a second vocabulary for the same word. Match core's register too:
Catalan and Spanish both take the infinitive for action labels (`Afegir una línia`,
`Añadir una línea`), while a message reporting what just happened takes the perfect.

**A module's own name and summary are translatable, but `i18n export` will never give them to you.**
`ir.module.module.shortdesc` and `summary` are `translate=True` and Odoo translates them wholesale —
`base`'s `es.po` carries 1,526 module names. They live in **base's** catalogue because
`ir_module.py`'s `create()` registers every module record as `base.module_<name>` with
`'module': 'base'`, so the exporter attributes them to base and omits them from ours. Write them in
by hand, in the `.pot` **as well as** each `.po`:

```
#. module: base
#: model:ir.module.module,shortdesc:base.module_<your module>
```

**The POT half is not decorative, and skipping it fails silently.** `PoFileReader.__init__` merges
every PO against its module's POT — the comment says the POT comments are the trustworthy ones — and
`__iter__` skips `entry.obsolete`. polib's `merge()` marks anything absent from the POT obsolete, so
a PO entry with no POT counterpart is dropped with no warning and the name just stays English. It
reads like a bad translation, not a missing one. **Re-running `i18n export` therefore un-translates
the module name**, so guard both entries with a test —
`vmk_language_systray/tests/test_language_systray.py` does, and also asserts the xmlid still belongs
to `base`, which is the premise the whole workaround rests on.

**Every module needs a catalogue, because every module has at least two untranslated terms.** Its
own name and summary, per the section above — and the exporter never shows them to you, so an empty
POT is not evidence there is nothing to translate. **Put them in the POT as well as every `.po`, and
guard them with a test.** This is the half that fails silently: `PoFileReader.__init__` merges each
PO against its module's POT and `__iter__` skips whatever polib's `merge()` marked obsolete, so a PO
entry with no POT counterpart is discarded without a warning and the module simply keeps its English
name. `vmk_event_sessions` shipped in exactly that state — both entries present in `es.po` and
`ca.po`, both dropped on load — until 22 September 2026. Every module now carries a
`TestModuleNameTranslation`, which checks the POT still has them, that both catalogues give them a
non-empty `msgstr`, and that the xmlid still belongs to `base`. Newer modules keep it in
`tests/test_translations.py`; the first seven put it at the foot of their own test file, which is
where to look.

This reverses an earlier rule here, which held that a module whose extracted terms all belong to
core needs no `i18n/` at all. That reasoning was sound as far as it went: extending a core model
attributes that model's name and its `display_name`/`id` fields to your module in the export, so a
POT can be entirely `Display Name`, `ID`, `Menu`, `Config Settings` — every one a record core
already translates. `vmk_settings_sort` was exactly that case and `vmk_apps_page_sort` exports
nothing whatsoever. But both still appeared in the Apps list under an English name in a Spanish
database, which is the thing a catalogue exists to prevent. Both now carry one.

What survives of the old rule: when a module's POT does carry core-owned terms, translate them with
core's own wording rather than afresh — and `vmk_apps_page_sort` shows the floor, a catalogue whose
entire contents are the two hand-written `base.module_*` blocks.

Export from the running harness, into the container's `/tmp`, and read the file back out:

```bash
cd "../Tech Stack/odoo-dev"
docker compose exec -T odoo sh -c \
    'odoo i18n export -d dev -l pot -o /tmp/<module>.pot <module> && cat /tmp/<module>.pot' \
    > /tmp/<module>.pot
```

`exec` skips the image's entrypoint, which would otherwise turn `HOST`/`USER`/`PASSWORD` into
`--db_host` and friends that the `i18n` subcommand rejects outright; the harness's config file
supplies the connection instead. `-o` into the container's `/tmp` because the export otherwise
writes into each module's own `i18n/`, which the harness mounts read-only. The module must be
installed for its terms to exist. **Compare the export with the committed POT rather than copying it
over**: `dev` can hold terms from data another branch installed and left behind, and the exporter
never writes the hand-kept `base.module_*` entries.

**A view's translation reaches only the views its entry names.** Each `#:` line on a
`model_terms:ir.ui.view,arch_db:` entry is a record the translation is applied to. Reusing an
existing msgid in another view — the same note on a second form — needs that view's reference line
added to the entry in the POT and every PO, or the second view stays English. Added 2026-09-24.

**Write catalogues the way the exporter does.** Odoo writes PO files with `polib` at its defaults
(`PoFileWriter`, `odoo/tools/translate.py`), wrapping at 78 columns, and sorts entries by msgid. An
entry hand-inserted anywhere else, or wrapped differently, turns the next re-export into a diff of
noise. The one exception is the `base.module_*` pair, which our guard test reads one line each.
Added 2026-09-24.

**`loadlang` wants the full locale code.** `-l es` works because a language's `url_code` is `es`,
but `-l ca` silently matches nothing and leaves Catalan inactive — it is `ca_ES`. The `.po` file
still gets the short name, `ca.po`, which Odoo matches to `ca_ES` on load.

**Build for accessibility, following core's own conventions.** Core is inconsistent — its list
delete control carries `aria-label="Delete row"` while its email field hides the mailto anchor with
`display: none` until hover, which no keyboard reaches — so copy what it does well and not what it
does poorly. What we hit building `vmk_partner_email_multiple`, all verified in the browser:

- **An icon-only control needs a real accessible name.** `title` on a view button becomes
  `data-tooltip` and nothing else, which no screen reader announces, and **`aria-label` in the arch
  never reaches the DOM** — `list_renderer.xml` instantiates `ViewButton` from a fixed prop list
  (`className`, `clickParams`, `icon`, `string`, `title`, `tabindex`…) and drops the rest. The
  server delivers the attribute faithfully, so it is dropped at render, not at load, which is what
  makes it hard to spot. Use `string` and hide the label visually.
- **Never hide a control with `display` or `visibility`.** Both remove it from the tab order and the
  accessibility tree, so the control does not exist for anyone not using a mouse. Hide with
  `opacity: 0`, which stays focusable, and reveal on `:focus-within` as well as `:hover`.
- **An accessible name must say what the control _does_, not what it currently reads.** Core is
  split on this: `switch_company_item.xml` gets it right with
  `t-att-aria-label="'Switch to ' + props.company.name"`, while `switch_company_menu.xml`'s toggle
  carries only the bare company name. Copy the former. A label that is just the current value
  announces as "Español, button" and tells a screen-reader user nothing, which bites hardest on an
  icon-only control where there is no visible text to fall back on. Keep the visible text as a
  substring of the label, per WCAG 2.5.3.
- **A selected-state class is not a selected state.** Core's global
  `:not(.dropstart) > .dropdown-item.selected` rule marks the active entry with `font-weight` and a
  FontAwesome glyph in a `:before`, neither of which reaches the accessibility tree. Pass
  `attrs="{ role: 'menuitemradio', 'aria-checked': … }"` — `attrs` is `DropdownItem`'s escape hatch,
  spread through `t-att` _after_ its static `role="menuitem"`, so the later value wins.
- **Systray icons need `fa-lg`.** Core's own carry it (`fa-lg fa-comments`, `fa-lg fa-clock-o`) and
  render at 18.41px; without it FontAwesome inherits 14px and the icon reads as visibly undersized
  beside them. Measure `getComputedStyle` against a neighbour rather than eyeballing a screenshot.
- **Check the rendered DOM, not the arch.** These failures are invisible in the source and in the
  arch alike.
- **An empty `.pot` can be a symptom rather than a fact.** A module whose only strings are database
  values legitimately needs no catalogue — but check that it is not empty _because_ nothing is being
  said to a screen reader. `vmk_language_systray` exported zero terms until its icon-only button
  gained a real accessible name, at which point it needed `i18n/` after all.

**Test the minimal install.** Before a module is called done, install it on a fresh scratch database
with only its declared dependencies — `DB=<scratch> ./odev init <module>` — run its tests with its
dependencies' own suites alongside (see _Things that will otherwise cost you an hour_), and drive it
in Chrome **there**, not only on `dev`. Then do the same in combination with our related modules.
`dev` carries dozens of modules, and any of them can supply something ours forgot to declare:
`vmk_event_slot_multiday` passed every test and a Chrome check on dev, where `vmk_event_sessions`
happened to put `date` in the slot form's arch, and was broken on a core-only database. Felix, 24
September 2026: _"you should always test a minimal case, esp when we build these public stand-alone
modules."_ Serving the scratch database needs `./odev db use <name>` and then `./odev up`, and Felix
to log in; switch back afterwards.

**Refuse a contradiction; do not guess.** Where a write contradicts state the module keeps
consistent — event dates that disagree with their sessions, an end date that disagrees with a day
count — refuse it with a `ValidationError` saying what to do instead, rather than silently picking a
winner. A guess that goes wrong surfaces later as someone else's confusing error. Added 2026-09-24.

**Test twice: automated, and in a real browser.** Every module carries tests; that is the floor, not
the ceiling. Anything touching a view, a widget, or a stylesheet also gets driven in Chrome through
`claude-in-chrome` before it is called done, because a whole class of failure never reaches a Python
test. Two from this repo: a `cursor` rule that lost silently to a `cursor-pointer` utility core
declares `!important`, and a template inheritance whose xpath is resolved **client-side**, so a
wrong one fails in the console rather than raising on install. Both looked correct in the source,
both passed every test, and both were wrong on screen. Check computed styles and the rendered DOM
rather than trusting a screenshot — a screenshot cannot show you a cursor or an accessible name.

Write tests that assert **behaviour, not ambient state**. A test asserting freshly-installed
ordering fails on any database whose users have used the feature; re-run the seeding hook inside the
test instead.

**Build a test's expected text with the formatter the code uses.** A refusal message or a name
carrying a date formats per language — `18:00` or `6:00 PM` — so compare against
`format_datetime(...)` / `format_date(...)` of the same value, never a literal, or the test fails in
another language. Added 2026-09-23.

Documentation ships in the same commit as the code, and each module's `README.md` should explain
_why the non-obvious parts are that way_ — which core method fights you, and where. That is the part
nobody can reconstruct from the diff.
