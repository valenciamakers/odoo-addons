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

## Promoting an address

The swap button beside each additional address exchanges it with the contact's primary one: the
promoted address becomes the primary, and the old primary is kept as an additional address so mail
from it still matches. Its label is cleared, because the label described the address that has just
left.

It draws `fa-exchange` rather than an up arrow deliberately. The row already carries a drag handle
for reordering, so a vertical arrow beside it reads as "move up one position" — the one thing the
button does not do.

This is the one place the module writes to `res.partner.email`, and it does not contradict the rule
above. The rule is that the module never writes there on its _own_ initiative, behind your back; a
button somebody presses is the user editing their own contact, with the bookkeeping done for them.
`email` carries `tracking=1` (`mail/models/res_partner.py:21`), so the swap appears in the chatter
by itself.

## The envelope, and why it needs a widget

Each row carries the same envelope the contact form puts beside the main email address, opening a
`mailto:` link in whatever mail client the browser hands it to. Nothing is sent through Odoo, so the
non-goal below still holds: the module never mails an additional address itself.

Getting it there is less obvious than naming a widget. Odoo registers two email widgets — `email`
and `form.email` — and the field registry resolves `widget="email"` to `form.email` in a **form**
view but to the plain `email` in a **list**. Only the form variant draws the envelope, and it does
so with an xpath onto `//input`, which exists only in the template's _edit_ branch. A list row that
nobody is editing renders the readonly branch, so neither widget can put an envelope there.

`vmk_email_link` therefore extends `EmailField` and replaces its readonly branch, which core renders
as a `mailto:` anchor carrying `t-on-click.stop`. That is wrong twice over for a list of addresses
you are maintaining: it makes the address itself a link, and the `.stop` swallows the click that
would otherwise open the cell for editing. The address becomes plain text and the envelope alone
sends mail, so clicking anywhere in the cell edits it, as in any other list.

The envelope appears on hover, which is what core's field does too — its `mailto:` anchor is
`display: none` until hovered, while a second, permanent envelope sits in front of the input as a
marker. We reveal ours with `visibility` rather than `display`, because `ms-auto` pushes it to the
right of the cell and reserving its box means revealing it never reflows the address beside it.

### Both controls take work to be reachable without a mouse

The envelope is revealed with `opacity`, not the `display` core uses or the `visibility` this had
first. Both of those drop the anchor out of the tab order and the accessibility tree, so a keyboard
or screen reader user could never reach it — the control would effectively not exist for them. At
`opacity: 0` it stays focusable, and a `:focus-within` rule on the row brings it into view when it
is tabbed to.

The swap button gets its accessible name from `string`, which the stylesheet then hides visually so
the control stays icon-only. Neither obvious alternative works: `title` becomes `data-tooltip` and
nothing else, which carries no accessible name, and an `aria-label` in the arch never reaches the
DOM at all — `list_renderer.xml:308-318` instantiates `ViewButton` from a fixed prop list
(`className`, `clickParams`, `icon`, `string`, `title`, `tabindex`…) that never passes the arch's
remaining attributes through. The arch keeps the attribute all the way to the client, which is what
makes this one hard to spot: it is dropped at render, not at load.

### The cursor rules need `!important`, and not for the usual reason

The list renderer stamps a `cursor-pointer` utility class onto every data cell, and that utility is
declared `!important`. An ordinary declaration therefore loses to it no matter how specific the
selector, which is silent and looks like the stylesheet not loading at all. Among `!important`
declarations specificity decides again, so the scoped rules in `email_link_field.scss` win.

The point of them: both text cells read as editable text, because that is what clicking one does,
and only the controls themselves are pointer — not the cells around them. The envelope's gap from
the label column is a margin rather than padding so that the pointer covers the icon and nothing
else. The drag handle keeps the grab cursor core gives it.

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

## Translations

`i18n/` carries the template and a Spanish catalogue; Odoo loads `i18n/*.po` on install with no
manifest entry. Terms this module shares with core — _Contact_, _Created by_, _Send Email_ — reuse
core's own Spanish wording rather than a second translation of the same word, so the module reads as
part of the backend.

Regenerating the template after changing any user-facing string:

```bash
cd dev
docker compose run --rm -e PGHOST=db -e PGUSER=odoo -e PGPASSWORD=odoo \
    -v "$PWD/../vmk_partner_email_multiple/i18n:/mnt/out" --entrypoint odoo odoo \
    i18n export -d test -o /mnt/out/vmk_partner_email_multiple.pot vmk_partner_email_multiple
```

Two harness details are doing work in that command. `--entrypoint odoo` is required because the
image's entrypoint translates `HOST`/`USER`/`PASSWORD` into `--db_host` and friends, which the
`i18n` subcommand rejects outright — hence passing the connection as libpq's `PG*` variables
instead. And `-o` is required because the export otherwise writes into each module's own `i18n/`
folder, which the harness mounts read-only.

Upgrade the module with the database's language loaded to see a change take effect; `-u` alone
reloads the `.po` but the terms only render for a user whose language is set.

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
