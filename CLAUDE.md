# CLAUDE.md — Odoo Modules

Odoo 19 modules for Valencia Makers: some third-party and under evaluation, some ours. Everything
here targets **Odoo 19 Enterprise, self-hosted** (Hetzner via oec.sh, Docker behind Traefik). See
`../.claude/CLAUDE.md` for the business context; this file wins inside this repo.

## Layout

- **`jfe_*`** — modules we author. `jfe_language_sequence` is the first; read its `README.md` before
  writing another, as it documents most of the traps below in context.
- **Everything else** — third-party modules under evaluation, vendored as downloaded. Do not tidy,
  reformat or "improve" them; a clean diff against what the vendor shipped is what makes the next
  upgrade reviewable.
- **`dev/`** — the local Odoo 19 test harness.

## Testing locally

The harness mounts the repo root as an addons path, so any module here installs by name.

```bash
cd dev
docker compose up -d db

# create a database and install a module (post_init_hook runs on install only)
docker compose run --rm odoo odoo -d test --init jfe_language_sequence \
    --without-demo=all --stop-after-init

# run that module's tests
docker compose run --rm odoo odoo -d test -u jfe_language_sequence \
    --test-enable --test-tags /jfe_language_sequence --stop-after-init

# interactive shell
docker compose exec -T odoo odoo shell -d test \
    --db_host=db --db_user=odoo --db_password=odoo --no-http

docker compose up -d odoo          # serve on localhost:8069
docker compose down                # tear everything down
```

Five things that will otherwise cost you an hour each:

- **Keep exactly one database.** With two, Odoo can no longer auto-select and serves the database
  selector instead — anonymous frontend requests then 404 and the website looks broken. Drop the
  spare (`docker compose exec db dropdb -U odoo --force <name>`) rather than debugging the site.
- **`docker compose exec` skips the entrypoint**, which is what translates `HOST`/`USER`/`PASSWORD`
  into CLI flags. Pass `--db_host=db --db_user=odoo --db_password=odoo` to anything run that way, or
  it will try a local socket and fail.
- **`odoo shell` does not signal cache invalidation to the running server.** `service/model.py` calls
  `registry.signal_changes()` after each RPC; the shell has no such hook, so a write there leaves
  other workers stale. Call `env.registry.signal_changes()` **before** `env.cr.commit()`, or restart
  the server. Getting this backwards looks exactly like a caching bug in your module.
- **The running server holds the Python it started with.** `docker compose restart odoo` after
  editing code, or you are testing the previous version.
- **There is no `--uninstall` flag.** Use `button_immediate_uninstall()` on the `ir.module.module`
  record from a shell, with the server stopped.

## Verify against source, not memory

Read the real 19.0 source before building on any claim about what Odoo does. It is right there in the
image:

```bash
docker run --rm odoo:19 bash -c "grep -rn 'def _get_frontend(' /usr/lib/python3/dist-packages/odoo/"
docker create --name odoo19src odoo:19
docker cp odoo19src:/usr/lib/python3/dist-packages/odoo/addons/base/models/res_lang.py .
```

**The `odoo-development` plugin's skill files are stale for 19.0** — they document `<tree>`
throughout, and claim type annotations are mandatory when core does not use them. Treat them as a
starting point, never as authority.

**Read the JavaScript too.** Ordering, drag behaviour and view composition are frequently decided in
`web/static/src/**`, not in Python. Half the surprises below live there.

## Odoo 19 traps, verified

**Views**

- `<tree>` became `<list>` in 18, but core **view record ids kept their old names** —
  `base.res_lang_tree` defines a `<list>`. Anchor an xpath on a named field
  (`<field name="x" position="before">`), never on the root tag, and it survives the rename.
- `attrs="{...}"` was removed in 17. Use direct attributes (`invisible="not active"`).
- Ship `static/description/index.html`. Without it `ir.module.module._get_desc()` falls back to
  running your `README.md` through **docutils as RST**, which spews parse errors on every install and
  renders the Apps description badly.
- `groups="base.group_no_one"` means developer mode. Several core screens are gated this way,
  including Settings → Translations → Languages.

**Models**

- An inherit-only module needs **no `security/ir.model.access.csv`** — ACLs are per model, and adding
  a field to an existing model inherits them. Generators emit one anyway; delete it.
- `models.Constraint()` replaces `_sql_constraints`.
- `post_init_hook(env)` takes the environment, and runs on **install only** — never on upgrade. If a
  hook seeds data, an upgrade will not re-seed it; apply it by hand when testing on an existing
  database.
- Check a field's declared default before relying on it. `res.lang.active` is
  `fields.Boolean()` with **no default**, so a hand-created language is disabled.

**Ordering, if you add a `sequence`**

- A list view carrying `widget="handle"` and no `default_order` gets `<handle field>, id` imposed by
  the **web client** (`web/static/src/views/list/list_arch_parser.js`), overriding the model's
  `_order` entirely. Your `_order` will not order that list.
- You cannot fix that with `default_order`: `canResequenceRows` only permits dragging when
  `orderBy[0].name` **is** the handle field. Any order starting with something else silently disables
  drag and drop. Grouping therefore has to live in the sequence *values*.
- **Seed distinct values.** On tied or non-monotonic sequences, `resequence()` in
  `web/static/src/model/relational_model/utils.js` sets `reorderAll` and rewrites the entire list;
  with strictly increasing values it rewrites only the records between the two drag positions.
- Cover `create()` as well as `write()`. A record created later takes the field default and lands
  wherever that points, reintroducing ties.

**Caches**

- Odoo caches by **name**: `'default'`, `'stable'`, and others. `Registry.clear_cache(*names)` clears
  whole groups, and the per-method `ormcache.clear_cache()` of older versions **is gone in 19** —
  there is no narrow invalidation.
- So prefer reading values from a cache that core already invalidates over clearing a broad one
  yourself. `res.lang.write()` clears `'stable'`; sorting on values from there avoided clearing
  `'default'` — every compiled QWeb template on the site — on each reorder.
- **`_order` is not the last word on ordering.** Core routinely sorts explicitly past it:
  `res.lang.get_installed()` goes through `search_fetch(..., order='name')` and
  `website._get_frontend()` uses `language_ids.sorted('name')`. Grep for the *consumers* of an
  ordering before assuming a model-level change reaches them.
- A custom `__getitem__` can break `in`. `LangDataDict` returns a dummy for unknown keys instead of
  raising, and `Mapping.__contains__` is built on `__getitem__` — so `key in it` is **always true**.
  Build a plain `dict` when you need real membership.

## Authoring conventions

Manifest: `"version": "19.0.1.0.0"` (Odoo series first), `"license": "LGPL-3"`,
`"author": "Valencia Makers, SL"`. Keep `depends` minimal and honest — depend on `website` only if
you override something it defines.

**Prettier config lives per module, never at the repo root.** Each `jfe_*` module carries its own
`.prettierrc` (`proseWrap: always`, `printWidth: 100`), as does `dev/`. Give every new `jfe_*` module
one.

This is deliberate rather than fussy. A config is what opts a directory into formatting, so placing
one only in the modules we author means **nothing can opt the vendored ones in** — not the hook, not
a stray `pnpm dlx prettier --write .` from the wrong directory. The alternative, a root config plus a
`.prettierignore` listing the vendored modules, would work (the global hook runs Prettier from the
config's own directory, so ignore files beside it apply), but it stays correct only as long as that
ignore file does. Given the point is a clean diff against what each vendor shipped, structural
protection beats a rule that has to keep being right.

The decisive reason is editors rather than anything about Claude Code. A format-on-save extension
resolves config the same way Prettier does — walking up from the file — and knows nothing about our
conventions or our hooks. A root config would hand every vendored module to it on the first save.
A missing config is the only protection that holds for tools we do not control.

The cost is that nothing at the root is opted in, which is why this file is hand-wrapped to 100
columns.

Write tests that assert **behaviour, not ambient state**. A test asserting freshly-installed ordering
fails on any database whose users have used the feature; re-run the seeding hook inside the test
instead.

Documentation ships in the same commit as the code, and each module's `README.md` should explain *why
the non-obvious parts are that way* — which core method fights you, and where. That is the part
nobody can reconstruct from the diff.

## Evaluating third-party modules

Plenty of paid modules are a field, a view inherit and fifty lines. Before buying, read `models/` and
ask what it does that `_inherit` plus a `sequence` field would not — then check whether it handles the
traps above (the client-imposed handle ordering, `create()` as well as `write()`, cache
invalidation). Those are what separate a module that works from one that appears to.

Judge the reverse honestly too: anything touching accounting, EDI, payment providers or Spanish tax
compliance carries regulatory risk and ongoing upgrade maintenance that is worth real money. The
question is never the line count on its own, it is whether the work is genuinely ours to redo.
