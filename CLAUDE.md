# CLAUDE.md — Odoo Addons

The Odoo 19 modules Valencia Makers writes and maintains, MIT licensed. They run against a
self-hosted **Odoo 19 Enterprise** instance but depend only on Community modules. See
`../.claude/CLAUDE.md` for the business context; this file wins inside this repo.

Third-party modules under evaluation live in a separate private repo (`../Odoo Addons - External`
locally), not here — this repo is publishable, so nothing enters it that we do not own. The two
remotes differ by one word, so check which one you are pushing to.

## Layout

- **`vmk_language_sequence`** — manual ordering of the enabled languages.
- **`vmk_language_freeze_meta`** — stops Odoo updates reverting edits to language metadata.
- **`vmk_apps_menu_sort`** — alphabetical ordering of the apps on the main menu.
- **`vmk_apps_page_sort`** — alphabetical ordering of the Apps page, by displayed name.
- **`vmk_settings_sort`** — alphabetical ordering of the Settings sidebar and Technical groupings.
- **`vmk_partner_email_multiple`** — several email addresses per contact, matched by Odoo's own
  machinery, and kept rather than dropped when contacts are merged.
- **`dev/`** — the local Odoo 19 test harness.

Read the existing modules' `README.md` files before writing another; between them they document most
of the traps below in context.

## Commits — this repo departs from the machine-wide rule

`~/.claude/rules/git-workflow.md` says to commit as `Claude <claude@pvt.jfe.xyz>` with no
`Co-Authored-By` trailer. **That does not apply here.** This repo is published, so its history
should attribute to the maintainer and link on GitHub, with assistance disclosed rather than
substituted for authorship.

- **Author and commit as Felix.** That is already the global git identity, so a plain `git commit`
  is correct — no `-c user.name=…` overrides.
- **Add one trailer to commits Claude wrote**, and nothing else — no "Generated with" line:

  ```
  Co-Authored-By: Claude <noreply@anthropic.com>
  ```

  Commits Felix writes get no trailer.

The whole history was rewritten to this convention on 2026-08-13 and is uniform; keep it that way.
Signing is unaffected — `commit.gpgsign` is on globally and signs with Felix's SSH key through
1Password whoever the author is, so commits still fail while the vault is locked, which is expected
and not worth investigating. The rewritten history is itself unsigned, because rewriting invalidates
signatures.

**Only this repo.** `../Odoo Addons - External` and every other repo keep the machine-wide
convention. Everything else in `git-workflow.md` still holds here: one topic per commit, imperative
subject, a `-` bullet body explaining the why, never `git add -A`, and never push — Felix does that.

## Testing locally

The harness mounts the repo root as an addons path, so any module here installs by name.

```bash
cd dev
docker compose up -d db

# create a database and install a module (post_init_hook runs on install only)
docker compose run --rm odoo odoo -d test --init vmk_language_sequence \
    --without-demo=all --stop-after-init

# run that module's tests
docker compose run --rm odoo odoo -d test -u vmk_language_sequence \
    --test-enable --test-tags /vmk_language_sequence --stop-after-init

# interactive shell
docker compose exec -T odoo odoo shell -d test \
    --db_host=db --db_user=odoo --db_password=odoo --no-http

docker compose up -d odoo          # serve on localhost:8069
docker compose down                # stop everything — DROPS EVERY DATABASE, see below
docker compose down -v             # the above, and drop the filestore volume too
```

Seven things that will otherwise cost you an hour each:

- **`docker compose down` destroys your databases.** Only the Odoo _filestore_ is a named volume;
  PostgreSQL's data directory is not, so it lives on the `db` container's writable layer and dies
  with it. `down` therefore discards every database while faithfully preserving the filestore of the
  databases it just deleted. Use `docker compose stop` to pause without losing them.
- **Both repos' harnesses are the same Compose project.** The project name comes from the directory,
  and this repo's harness and `../Odoo Addons - External/dev` are both called `dev` — so they share
  the container names `dev-db-1` / `dev-odoo-1` and the `dev_` volume namespace. Only one can run at
  a time, and bringing one down to start the other takes the first one's databases with it (see
  above). Expect to recreate the database whenever you switch repos.

- **Keep exactly one database.** With two, Odoo can no longer auto-select and serves the database
  selector instead — anonymous frontend requests then 404 and the website looks broken. Drop the
  spare (`docker compose exec db dropdb -U odoo --force <name>`) rather than debugging the site.
- **`docker compose exec` skips the entrypoint**, which is what translates `HOST`/`USER`/`PASSWORD`
  into CLI flags. Pass `--db_host=db --db_user=odoo --db_password=odoo` to anything run that way, or
  it will try a local socket and fail.
- **`odoo shell` does not signal cache invalidation to the running server.** `service/model.py`
  calls `registry.signal_changes()` after each RPC; the shell has no such hook, so a write there
  leaves other workers stale. Call `env.registry.signal_changes()` **before** `env.cr.commit()`, or
  restart the server. Getting this backwards looks exactly like a caching bug in your module.
- **The running server holds the Python it started with.** `docker compose restart odoo` after
  editing code, or you are testing the previous version.
- **There is no `--uninstall` flag.** Use `button_immediate_uninstall()` on the `ir.module.module`
  record from a shell, with the server stopped.
- **A fixture created and then modified inside one flush cycle produces no tracked change.**
  Tracking compares against the values at the last flush, so a `TransactionCase` that creates a
  record in `setUpClass` and writes to it in the test sees an empty chatter and looks like a
  tracking bug in your code. Flush between the two — `self.env.flush_all()` then `self.cr.flush()`,
  which is all `MailCommon.flush_tracking()` does.

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
- **A `state="code"` server action only shows its Run button when `model_id` is `ir.actions.server`
  itself.** `view_server_action_form` carries
  `invisible="model_name != 'ir.actions.server' or state != 'code'"`, and `model_name` is
  `related='model_id.model'`. Bind a standalone action to the model its code happens to touch and it
  stays callable from `run()` — so a test calling `run()` still passes — while being unreachable
  from the interface entirely. Assert `model_name` in the test, not just that it runs.

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

Manifest: `"version": "19.0.1.0.0"` (Odoo series first), `"author": "Valencia Makers, SL"`. Keep
`depends` minimal and honest — depend on `website` only if you override something it defines.

**We license our modules MIT**, declared as `"license": "Other OSI approved licence"` (British
spelling, exactly that string) with the MIT text in a `LICENSE` file beside the manifest. Odoo
validates `license` against a fixed `Selection` on `ir.module.module` that has **no MIT entry**, and
the failure is silent: module loading bypasses the ORM, so `"license": "MIT"` installs cleanly and
leaves an invalid value in the database that renders blank in the Apps list and raises
`ValueError: Wrong value for ir.module.module.license` the moment anything writes that field.

Nothing obliges us to copyleft. Odoo Community is LGPL-3, which exists to let works that merely
_use_ the library carry any license, and Odoo SA's own position permits proprietary modules. Two
conditions to keep true: do not copy Odoo source into a module (override by calling `super()`,
rather than copy-pasting a core method to tweak it — the copied block would stay LGPL), and do not
depend on an Enterprise module, which would put distribution under OEEL whatever the manifest says.

**MIT is the default, not a rule.** An individual module may ship under a GPL variant where that is
the better trade, and the decision is per module rather than per repo. Weigh it explicitly, the way
`vmk_partner_email_multiple` weighed wrapping `super()` against copying core, and record the
reasoning in that module's `README.md` — a licence with no stated reason is one nobody can revisit
safely. Three cases where copyleft is the honest answer rather than a concession:

- **The module genuinely needs to copy core implementation.** Where an override cannot express the
  change and a core method has to be lifted and edited, that block stays LGPL-3. Relicensing the
  module to match is more honest than contorting the design to avoid the copy, or shipping MIT over
  code that is not ours to relicense.
- **We want it upstreamed to the OCA**, whose repository policy requires LGPL-3 or AGPL-3. That is
  policy rather than legal consequence, and we hold the copyright either way — but a module intended
  for them may as well be born under it.
- **We want derivatives to stay open**, which is a preference we are entitled to hold per module.

Odoo validates the manifest string against a fixed `Selection`, so use its exact values — `LGPL-3`,
`AGPL-3`, `GPL-3`, `GPL-3 or any later version` — and put the matching licence text in `LICENSE`.
Only MIT needs the `Other OSI approved licence` workaround above, because only MIT is missing from
that list.

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

**A module whose only extracted terms belong to core needs no catalogue at all.** Extending a core
model attributes that model's name and its `display_name`/`id` fields to your module in the export,
so a POT can be entirely `Display Name`, `ID`, `Menu`, `Config Settings` — every one of them a
record core already translates. `vmk_settings_sort` is exactly this case and `vmk_apps_page_sort`
exports nothing at all; both deliberately have no `i18n/`. Check the POT for a term you actually
wrote before adding files.

Exporting needs two workarounds, both harness-specific:

```bash
cd dev
docker compose run --rm -e PGHOST=db -e PGUSER=odoo -e PGPASSWORD=odoo \
    -v "$PWD/../<module>/i18n:/mnt/out" --entrypoint odoo odoo \
    i18n export -d test -o /mnt/out/<module>.pot <module>
```

`--entrypoint odoo` because the image's entrypoint turns `HOST`/`USER`/`PASSWORD` into `--db_host`
and friends, which the `i18n` subcommand rejects outright — hence passing the connection as libpq
`PG*` variables. And `-o` because the export otherwise writes into each module's own `i18n/`, which
the harness mounts read-only. The module must be installed for its terms to exist.

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
- **Check the rendered DOM, not the arch.** These failures are invisible in the source and in the
  arch alike.

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

Documentation ships in the same commit as the code, and each module's `README.md` should explain
_why the non-obvious parts are that way_ — which core method fights you, and where. That is the part
nobody can reconstruct from the diff.
