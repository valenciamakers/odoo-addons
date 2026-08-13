# vmk_partner_email_multiple — plan

Several email addresses per contact, matched by Odoo's own machinery. **Nothing is built yet**; this
file is the agreed shape, to be deleted once `README.md` describes the real thing.

The technical name was checked free on the Apps Store on 2026-08-13 (404 for
`vmk_partner_email_multiple`, against a 200 control probe of `kw_mock_mail_server`).

## The problem

One contact, several addresses. Mail arriving from any of them should land on that contact rather
than minting a duplicate — which is what happens today, most visibly with `noreply@` senders.

Odoo has no native support for this. The comma-separated `email` field looks like support and is
not: `email_normalized` is computed with `strict=False`, so it keeps **only the first address**, and
matching searches `email_normalized`. A comma list therefore improves matching in neither core Odoo
nor Mailflow, while making `email_formatted` emit `"Name" <a@x.com,b@y.com>` — a form core's own
docstring calls invalid and merely tolerated by some servers.

## Shape

Additive, not a replacement. `res.partner.email` keeps its core definition and meaning: the primary
address, plain `Char`, tracked, writable by anything. **The module never writes to it.** A child
table holds _additional_ addresses, and matching is widened to consider them.

That is the whole design decision, and it is what separates this from the alternatives surveyed (see
[Prior art](#prior-art)). Uninstall the module and every contact still has a valid primary address;
no other module's writes are fought.

### Model

`vmk.partner.email` — `partner_id` (m2o, `ondelete='cascade'`), `email`, `email_normalized` (stored,
`index=True`), a label, and a `sequence`.

- **No database-level unique constraint.** See the merge trap below — a DB constraint turns a merge
  collision into silent mass deletion. Enforce uniqueness per contact in Python with
  `@api.constrains`.
- **The same address may appear on several contacts.** Core permits it and the mail helpers have a
  documented tie-break for it; we do not add a restriction core does not have.
- An address already held as the contact's primary should not be duplicated as a child row.

### Matching overrides

All three route through one shared resolver, so behaviour cannot drift between them:

| Method                           | Where                             | Why                                             |
| -------------------------------- | --------------------------------- | ----------------------------------------------- |
| `_find_or_create_from_emails`    | `mail/models/res_partner.py:118`  | the real implementation; both halves, see below |
| `find_or_create`                 | `mail/models/res_partner.py:96`   | legacy single-address path, searches separately |
| `_mail_find_partner_from_emails` | `mail/models/mail_thread.py:2145` | repeats the same filter independently           |

**Widening the search is not sufficient**, and this is the trap that makes the module non-trivial.
`_find_or_create_from_emails` searches `[('email_normalized', 'in', [...])]` at line 175, but then
resolves each input address back to a partner at lines 222–232 by comparing
`partner.email_normalized == email_normalized`. Make the search succeed via the child table and that
final step still returns an empty recordset. Both halves need overriding: the domain **and** the
resolution loop, which must compare against the union of the contact's addresses.

### Merge integration

The workflow this module has to fit is Odoo's built-in contact merge, since that is how duplicates
already get cleaned up. Most of it is free:

- **`_update_foreign_keys` re-points every FK to `res_partner` in raw SQL**
  (`base/wizard/base_partner_merge.py:119-181`), discovered from the schema. Our `partner_id` column
  is one, so child rows migrate to the surviving contact with no code from us.
- **`_update_values` drops the source contacts' `email`** (`:341-392`). It skips o2m/m2m and
  computed fields, and for plain fields takes the last truthy value with the destination last — so
  the destination's address wins and the merged-away ones are simply lost. **That single gap is the
  feature**: override `_merge`, capture `src_partners.mapped('email')` _before_ `super()` (the
  sources are unlinked at `:471`), then create child rows for anything not already present.
- **Relax the same-email guard.** `_merge` refuses when the contacts differ by email (`:439-440`),
  which is every case this module exists for. Admins are exempt two lines earlier
  (`if self.env.is_admin(): extra_checks = False`), so it does not bite Felix, but it blocks any
  non-admin staff member.

### Search

Secondary addresses should be findable from the contacts autocomplete. `_rec_names_search`
(`base/models/res_partner.py:189`) takes field names on the model, so this needs either a non-stored
`Char` with a `search=` method added to that list, or an override of `_search_display_name`.

## Deliberate non-goals

Documented in `README.md` when built, not silently omitted. Each keeps reading the primary address
only:

- **Sending.** Additional addresses mean "we also know them here", never "mail them here".
  `email_formatted` is untouched.
- **Blacklist.** `mail.blacklist` keys on an address string and is consulted only by mass mailing
  and SMS — `mail/models/mail_mail.py` never checks it, so transactional mail is unaffected. A
  secondary address could be blacklisted while `partner.is_blacklisted` still reads false. Revisit
  if we ever send marketing mail, where GDPR obliges honouring opt-outs.
- **Bounce counters and mail-loop detection**, which query `email_normalized` with raw domains
  (`mail/models/mail_thread.py:814, 955, 998, 1016, 1756`).

## Prior art

Both alternatives were read in full before choosing the shape above.

- **OCA has nothing for this on 19.0.** `partner-contact` carries `partner_email_check`,
  `partner_email_duplicate_warn`, and `partner_phone_secondary` (a second phone `Char`). No
  `partner_multi_email` exists in the 14.0–19.0 branches. There is no maintained base to fork.
- **`partner_multiple_email_management_confianz`** (free, vendored in `../Odoo Addons - External`)
  is the comma-list with a UI: every child write joins all addresses and writes them back into
  `partner.email` via `sudo()`. It overrides no matching method at all, so it does not address the
  problem — and it makes every outbound header invalid, which is an active regression.
- **Smile's `contacts_multiple_contact_points`** (18.0) redefines `email`/`phone`/`mobile` as stored
  computes over a contact-point o2m. It never touches `_find_or_create_from_emails` either, so
  inbound matching still uses the default address only; it needed manual recompute calls bolted into
  `create`/`write` to work at all; and it redefines `mobile`, which **does not exist on
  `res.partner` in 19**.

## Mailflow

`unified_mail_client` bypasses Odoo's matching entirely — `[('email', '=ilike', addr)]` on the raw
column, in three places — so this module alone will not stop it creating duplicates. A patch routing
it through the core helper is written and ready to send upstream
(`../Odoo Addons - External/patches/`). If accepted, this module works with Mailflow automatically
and no bridge is needed. If declined, a `vmk_partner_email_multiple_mailflow` bridge goes in
`../Odoo Addons - Private`, which cannot be published because it would depend on OPL-1 code.

## Open questions

- Does an additional address need an `active` flag, or is deleting the row enough?
- Should the merge absorb a source contact's address even when it is invalid or unparseable?
- Is a per-address free-text label enough, or is a selection (billing, personal, noreply) better?

## Files to create

`__init__.py`, `__manifest__.py` (`"version": "19.0.1.0.0"`, `"author": "Valencia Makers, SL"`,
`"license": "Other OSI approved licence"`, `depends` on `mail` only), `LICENSE` (MIT), `README.md`,
`.prettierrc`, `models/`, `views/`, `security/ir.model.access.csv` (**needed here** — unlike our
inherit-only modules, this one adds a new model), `static/description/index.html`, and `tests/`.
