# Multiple Contact Emails (`vmk_partner_email_multiple`)

Several email addresses per contact, matched by Odoo's own machinery. Mail arriving from any of a
contact's addresses lands on that contact instead of minting a duplicate.

## The problem

Odoo has no native support for this. The `email` field accepts a comma-separated list, which looks
like support and is not:

- `email_normalized` is computed with `email_normalize(..., strict=False)`, which keeps **only the
  first address** of a list — and matching searches `email_normalized`. So every address after the
  first is unmatchable.
- `_compute_email_formatted` meanwhile renders the whole list as `"Name" <a@x.com,b@y.com>`, a form
  core's own docstring calls invalid and merely tolerated by some servers.

A comma list therefore improves matching not at all, while breaking outbound headers.

## What it does

A child table, `vmk.partner.email`, holds each contact's **additional** addresses, and the three
methods Odoo matches inbound mail with are widened to consider them.

`res.partner.email` keeps its core definition and meaning throughout: the primary address, a plain
`Char`, tracked, writable by anything. **The module never writes to it on its own initiative.** That
is the design decision the rest follows from — uninstall the module and every contact still has a
valid primary address, and no other module's writes are fought.

Where an address is held as one contact's primary and another's additional, **the primary wins**.
Installing this module never re-routes mail that core already matched correctly.

## Why the non-obvious parts are that way

### Widening the search is not enough

This is the trap that makes the module more than a `search()` override.
`res.partner._find_or_create_from_emails` (`mail/models/res_partner.py:118`) searches
`[('email_normalized', 'in', [...])]` at `:175` — but then, at `:222-232`, resolves each input
address back to a partner by comparing `partner.email_normalized == email_normalized`. Satisfy the
domain through the child table and that final step **still hands back an empty recordset**. Both
halves need dealing with, in all three entry points:

| Method                           | Where                             | What it needs                        |
| -------------------------------- | --------------------------------- | ------------------------------------ |
| `_find_or_create_from_emails`    | `mail/models/res_partner.py:118`  | both halves; the real implementation |
| `find_or_create`                 | `mail/models/res_partner.py:96`   | legacy path, searches separately     |
| `_mail_find_partner_from_emails` | `mail/models/mail_thread.py:2145` | the resolution half only — see below |

The third one needs less than it looks. In 19 it delegates its search to `_partner_find_from_emails`
(`:2156-2165`), which funnels everything through `_find_or_create_from_emails` at `:2094` — so the
mail gateway, author resolution, and recipient resolution are all covered by the first override.
What it still does on its own is re-resolve by `p.email_normalized == email_key` at `:2173`, which
drops the very partner core just found for us.

All three route through one resolver, `vmk.partner.email._resolve_partners`, so their behaviour
cannot drift apart.

### The overrides wrap `super()` rather than reimplementing it

Each one resolves the addresses it can, passes only the rest to `super()`, and splices the two
result lists back into input order. Per-email resolution cannot cross-contaminate, because core
matches each input against its own normalized value.

Copying `_find_or_create_from_emails` and widening both halves in place would be the obvious
approach and is the wrong one twice over: it would leave LGPL source inside an MIT module, and it
would silently stop tracking whatever Odoo changes in that method next.

### There is deliberately no unique constraint, on any column

The tempting one is `unique(partner_id, email_normalized)`. It is precisely the one that must not
exist. `_update_foreign_keys_generic` (`base/wizard/base_partner_merge.py:119-181`) re-points every
foreign key to `res_partner` in raw SQL, and at `:167` asks `_has_check_or_unique_constraint()`
whether any CHECK or UNIQUE constraint touches the column it is about to update — `partner_id`. If
one does, the `UPDATE` runs inside a savepoint whose `except psycopg2.Error` handler falls back to:

```sql
DELETE FROM vmk_partner_email WHERE partner_id IN <every source id>
```

One colliding address during a contact merge would therefore destroy **every** additional address of
**every** source contact, not just the conflicting row. Uniqueness lives in `_check_email_unique`
instead, which that raw SQL bypasses anyway.

The same address may still appear on several contacts. Core permits that and the mail helpers have a
documented tie-break for it, so we add no restriction core does not have.

### The merge keeps addresses that core would drop

Odoo's built-in contact merge is how duplicates actually get cleaned up, so the module has to fit
that workflow. Most of it is free: `_update_foreign_keys` discovers our `partner_id` column from the
schema, so child rows follow the surviving contact with no code from us.

The gap is `_update_values` (`:341-392`), which skips o2m/m2m and computed fields and, for plain
fields, takes the last truthy value with the destination last — so the destination's `email` wins
and every merged-away address is simply lost. **That single gap is the feature**: `_merge` is
overridden to capture the addresses first and re-create them as additional ones afterwards.

They have to be captured _before_ `super()`, because the source contacts are unlinked at `:471`. The
destination cannot be captured that early — when the wizard passes none, core picks it itself at
`:446-448` — so every candidate's address is captured and the survivor is identified afterwards.

### Searching by dotted path

`_rec_names_search` (`base/models/res_partner.py:189`) does accept dotted paths —
`_search_display_name` resolves the last field in the chain (`orm/models.py:1462-1473`) — so
`vmk_email_ids.email` works as an entry and no helper field is needed. But _appending_ to a class
attribute means restating core's whole list and silently losing whatever Odoo adds to it later, so
`_search_display_name` is overridden and the domains combined instead, with the same aggregator core
chooses at `:1460`.

## Known limitation: merging as a non-admin

`_merge` refuses when the contacts differ by email (`base/wizard/base_partner_merge.py:439-440`) —
which is every case this module exists for. Admins are exempted two lines earlier
(`if self.env.is_admin(): extra_checks = False`), so it does not bite an administrator, but a
non-admin staff member cannot merge two contacts into one and keep both addresses.

This is left alone deliberately. Relaxing it means forcing `extra_checks=False`, which would also
pre-disable any future check Odoo puts behind that flag. Revisit when someone other than an
administrator actually needs to do contact cleanup.

## Deliberate non-goals

Each of these keeps reading the primary address only:

- **Sending.** An additional address means "we also know them here", never "mail them here".
  `email_formatted` is untouched.
- **Blacklist.** `mail.blacklist` keys on an address string and is consulted only by mass mailing
  and SMS — `mail/models/mail_mail.py` never checks it, so transactional mail is unaffected either
  way. An additional address could be blacklisted while `partner.is_blacklisted` still reads false.
  Revisit if we ever send marketing mail, where GDPR obliges honouring opt-outs.
- **Bounce counters and mail-loop detection**, which query `email_normalized` with raw domains
  (`mail/models/mail_thread.py:814, 955, 998, 1016, 1756`).

## Mailflow

`unified_mail_client` bypasses Odoo's matching entirely — `[('email', '=ilike', addr)]` on the raw
column, in three places — so this module alone will not stop it creating duplicates. A patch routing
it through the core helper is ready to send upstream; if accepted, this module works with Mailflow
automatically.

## Testing

```bash
cd dev
docker compose run --rm odoo odoo -d test --init vmk_partner_email_multiple \
    --without-demo=all --stop-after-init
docker compose run --rm odoo odoo -d test -u vmk_partner_email_multiple \
    --test-enable --test-tags /vmk_partner_email_multiple --stop-after-init
```

## License

MIT. See `LICENSE`. Declared in the manifest as `"Other OSI approved licence"`, which is the only
value Odoo's `Selection` accepts for it.
