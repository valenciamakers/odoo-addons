# Odoo Modules

Odoo modules for Valencia Makers: some third-party and under evaluation, some ours. Everything here
targets **Odoo 19 Enterprise, self-hosted** (Hetzner via oec.sh, Docker behind Traefik).

## Layout

- **`jfe_*`** — modules we author. `jfe_language_sequence` is the first; see its `README.md` before
  writing another, as it documents several traps discovered during development.
- **Everything else** — third-party modules under evaluation, vendored as downloaded. Do not tidy,
  reformat or "improve" them; a clean diff against what the vendor shipped is what makes the next
  upgrade reviewable.
- **`dev/`** — the local Odoo 19 test harness.

## Authoring conventions

Manifest: `"version": "19.0.1.0.0"` (Odoo series first), `"license": "LGPL-3"`,
`"author": "Valencia Makers, SL"`. Keep `depends` minimal and honest; depend on `website` only if
you override something it defines.

**Prettier config lives per module, never at the repo root.** Each `jfe_*` module carries its own
`.prettierrc` (`proseWrap: always`, `printWidth: 100`), as does `dev/`. Every new `jfe_*` module
should get its own file.

## Licensing

This repository contains modules for which we own the copyright, and third-party modules with
various licensing terms. Therefore if we ever decide to release our own modules publicly, they will
need to be moved into a "clean" repository.
