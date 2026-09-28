# Multiple Contact Emails (`vmk_partner_email_multiple`)

Assign multiple email addresses to a contact, and Odoo matches mail from all of them. In standard
Odoo, a contact can have only one email address, and mail from another address is treated as a
unique sender, resulting in duplicate contacts. With this module, mail from any of a contact's
additional addresses is matched to the same contact record, including mail that creates a lead, an
applicant, or a ticket.

**How to use it** is in the user documentation, [`doc/index.rst`](doc/index.rst), which the Odoo
Apps Store also shows on the module's page, together with the changelog.

It depends only on `mail` (_Discuss_), and works on Community and Enterprise alike. LGPL-3, © 2026
Valencia Makers, SL.

## For developers

What follows is how the module works and why it is built this way: what core does, which of its
methods this relies on, and the traps found on the way.

### The problem

Odoo has no native support for this. The `email` field accepts a comma-separated list, which looks
like support and is not:

- `email_normalized` is computed with `email_normalize(..., strict=False)`, which keeps **only the
  first address** of a list — and matching searches `email_normalized`. So every address after the
  first is unmatchable.
- `_compute_email_formatted` meanwhile renders the whole list as `"Name" <a@x.com,b@y.com>`, a form
  core's own docstring calls invalid and merely tolerated by some servers.

A comma list therefore improves matching not at all, while breaking outbound headers.

### What it does

A child table, `vmk.partner.email`, holds each contact's **additional** addresses, and the three
methods Odoo matches inbound mail with are widened to consider them.

`res.partner.email` keeps its core definition and meaning throughout: the primary address, a plain
`Char`, tracked, writable by anything. **The module never writes to it on its own initiative.** That
is the design decision the rest follows from — uninstall the module and every contact still has a
valid primary address, and no other module's writes are fought.

Where an address is held as one contact's primary and another's additional, **the primary wins**.
Installing this module never re-routes mail that core already matched correctly.

### Promoting an address

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
`email` carries `tracking=1` (`mail/models/res_partner.py:20`), so the swap appears in the chatter
by itself.

### The envelope, and why it needs a widget

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

#### Both controls take work to be reachable without a mouse

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

#### The cursor rules need `!important`, and not for the usual reason

The list renderer stamps a `cursor-pointer` utility class onto every data cell, and that utility is
declared `!important`. An ordinary declaration therefore loses to it no matter how specific the
selector, which is silent and looks like the stylesheet not loading at all. Among `!important`
declarations specificity decides again, so the scoped rules in `email_link_field.scss` win.

The point of them: both text cells read as editable text, because that is what clicking one does,
and only the controls themselves are pointer — not the cells around them. The envelope's gap from
the label column is a margin rather than padding so that the pointer covers the icon and nothing
else. The drag handle keeps the grab cursor core gives it.

### Why the non-obvious parts are that way

#### Widening the search is not enough

This is the trap that makes the module more than a `search()` override.
`res.partner._find_or_create_from_emails` (`mail/models/res_partner.py:112`) searches
`[('email_normalized', 'in', [...])]` at `:161` — but then, at `:199-208`, resolves each input
address back to a partner by comparing `partner.email_normalized == email_normalized`. Satisfy the
domain through the child table and that final step **still hands back an empty recordset**. Both
halves need dealing with, in all three entry points:

| Method                           | Where                             | What it needs                        |
| -------------------------------- | --------------------------------- | ------------------------------------ |
| `_find_or_create_from_emails`    | `mail/models/res_partner.py:112`  | both halves; the real implementation |
| `find_or_create`                 | `mail/models/res_partner.py:89`   | legacy path, searches separately     |
| `_mail_find_partner_from_emails` | `mail/models/mail_thread.py:2041` | both halves too — see below          |

**The third one is different on 18, and worse than it looks.** On 19 this method delegates its
search to `_partner_find_from_emails`, which funnels everything through
`_find_or_create_from_emails` — so widening the first override was enough to cover the mail gateway,
author resolution, and recipient resolution together, and only the resolution half needed patching.
**On 18 there is no such delegation.** `_mail_find_partner_from_emails` has its own three-step
search — followers, then `_mail_search_on_user` (users, matched on `res.users.email`, which is
`related='partner_id.email'`, so an additional address never appears there either), then
`_mail_search_on_partner`, a plain `[('email_normalized', 'in', [...])]` domain (`:1986-1990`) — and
none of it touches `_find_or_create_from_emails`.

Widening `_mail_search_on_partner` alone still is not enough, and this is where 18 gets a second
trap on top of the first: the method's own final step (`:2108-2116`) re-matches every candidate it
collected by `partner.email_normalized == normalized_email` — the _partner's own_ normalized
address, not whatever got it into the candidate list. A partner found only because one of their
additional addresses matched fails that comparison and is dropped again, on the way out of the very
method that just found them — confirmed in the harness with `_mail_search_on_partner` overridden and
nothing else: the internal search returned the contact, and `_mail_find_partner_from_emails` still
returned an empty recordset. Worse, with `force_create=True` (what the gateway passes for an
unrecognised sender) that same final step then creates a **second, duplicate** contact, because its
own `partner` variable is still empty when it checks whether to create one.

So this override resolves what it can itself, _before_ calling `super()` at all, and hands only the
rest on — with the original `records`, `force_create`, and `extra_domain` untouched for that
remainder. The same shape as `_find_or_create_from_emails`, for the same reason: patching the result
of `super()` cannot fix a bug in how that method builds its own result.

All three route through one resolver, `vmk.partner.email._resolve_partners`, so their behaviour
cannot drift apart.

**Also 18-specific: `_find_or_create_from_emails` takes fewer arguments here.** `ban_emails`,
`filter_found`, `no_create`, `sort_key`, and `sort_reverse` were added to core's version of the
method after 18, so 18's signature is just `(self, emails, additional_values=None)`. None of that
filtering can be offered honestly through this override either — an address this module cannot
resolve still falls through to `super()`, which always creates, so a caller expecting
`no_create=True` to hold everywhere would be misled. Dropped, along with the tests that exercised
them.

#### The overrides wrap `super()` rather than reimplementing it

Each one resolves the addresses it can, passes only the rest to `super()`, and splices the two
result lists back into input order. Per-email resolution cannot cross-contaminate, because core
matches each input against its own normalized value.

Copying `_find_or_create_from_emails` and widening both halves in place would be the obvious
approach and is the wrong one: it would silently stop tracking whatever Odoo changes in that method
next.

#### There is deliberately no unique constraint, on any column

The tempting one is `unique(partner_id, email_normalized)`. It is precisely the one that must not
exist, though the reason is different on 18 than the mechanism this argument used on 19.

`_update_foreign_keys_generic` (`base/wizard/base_partner_merge.py:103-159`) re-points every foreign
key to `res_partner` in raw SQL. On 18 **it never asks whether a constraint exists** — that check
was added later. Instead, at `:120-129`, it counts the table's columns other than the one being
re-pointed. With only one, it takes a per-record `UPDATE` guarded by `NOT EXISTS` (`:135-149`); with
more than one — this table has nine (`email`, `email_normalized`, `label`, `sequence`, `id`, and the
four ORM housekeeping columns) — it always takes the branch at `:150-159`: a single bulk

```sql
UPDATE vmk_partner_email SET partner_id = %s WHERE partner_id IN %s
```

wrapped in a savepoint whose `except psycopg2.Error` falls back to
`DELETE FROM vmk_partner_email WHERE partner_id IN <every source id>` (`:158`). Our table always
takes this branch — the column count makes that certain, whatever we do to the schema. What we
control is whether the `UPDATE` can fail at all: with no unique or check constraint on `partner_id`,
there is nothing for it to violate, so it never raises `psycopg2.Error` for this table, and the
`DELETE` fallback is never reached. **No address is ever deleted by a merge on 18** — but for a
different reason than on 19, where staying constraint-free kept the branch itself from being chosen.
Here the branch is chosen regardless; staying constraint-free is what keeps it harmless.

What a constraint-free bulk `UPDATE` does **not** do is deduplicate. It has no per-value comparison,
so two source contacts that each hold the same address — or one that duplicates the destination's
own primary or additional address — leave the survivor holding two rows for one value, silently: the
ORM-level `_check_email_unique` constraint that would normally refuse that never runs, because raw
SQL bypasses it. See _The merge keeps addresses that core would drop_ below for how this module
closes that gap.

The same address may still appear on several contacts. Core permits that and the mail helpers have a
documented tie-break for it, so we add no restriction core does not have.

#### The merge keeps addresses that core would drop

Odoo's built-in contact merge is how duplicates actually get cleaned up, so the module has to fit
that workflow. Most of it is free: `_update_foreign_keys` discovers our `partner_id` column from the
schema, so child rows follow the surviving contact with no code from us.

The gap is `_update_values` (`:314-364`), which skips o2m/m2m and computed fields and, for plain
fields, takes the last truthy value with the destination last — so the destination's `email` wins
and every merged-away address is simply lost. **That single gap is the feature**: `_merge` is
overridden to capture the addresses first and re-create them as additional ones afterwards.

They have to be captured _before_ `super()`, because the source contacts are unlinked at `:444`. The
destination cannot be captured that early — when the wizard passes none, core picks it itself at
`:415-421` — so every candidate's address is captured and the survivor is identified afterwards.

**A second gap, found while porting to 18 but just as present on 19: the migration can leave a
genuine duplicate.** `_update_foreign_keys_generic`'s bulk `UPDATE` (previous section) has no
per-value comparison, so two source contacts holding the same additional address, or one duplicating
the destination's own address, land as two rows for one value on the survivor —
`_check_email_unique` never gets a chance to refuse it, because raw SQL bypasses the ORM entirely.
`_merge` now also calls `ResPartner._vmk_dedupe_emails()` on the survivor after every successful
merge of two or more contacts, not only when there was a primary address to absorb: it drops any row
that duplicates the contact's own primary, and any but the first of several rows sharing a
normalized address. `tests/test_merge.py` proves both the migration (no address lost) and the dedupe
(no address kept twice).

#### Searching by dotted path

`_rec_names_search` (`base/models/res_partner.py:198`) does accept dotted paths —
`_search_display_name` resolves the last field in the chain (`models.py:1843-1850`) — so
`vmk_email_ids.email` works as an entry and no helper field is needed. But _appending_ to a class
attribute means restating core's whole list and silently losing whatever Odoo adds to it later, so
`_search_display_name` is overridden and the domains combined instead, with the same aggregator core
chooses at `:1841`. On 18 there is no `odoo.fields.Domain` class — it was added in 19 — so both
core's own method and this override build plain list domains and combine them with
`odoo.osv.expression.AND` / `OR`.

That covers the autocomplete and the search panel's **Name** entry, which filters on `display_name`.
It does not cover its **Email** entry, which is a separate mechanism: `base.view_res_partner_filter`
gives that field `filter_domain="[('email', 'ilike', self)]"`, consulting the raw column and nothing
else. The search view is inherited to widen that domain as well, which is why both entries find an
additional address.

Widening the domain is the right move here rather than touching what `('email', ...)` means. The
field keeps its core meaning everywhere, and core reads it directly in places that matter — the
legacy `find_or_create` searches `[('email', '=ilike', ...)]` — so redefining it globally would
change matching behaviour far outside the search panel.

The Contacts app's own action points at that same search view (`contacts/views/contacts_views.xml`),
so one inherited view fixes the search people actually use.

### Known limitation: merging as a non-admin

`_merge` refuses when the contacts differ by email (`base/wizard/base_partner_merge.py:413`) — which
is every case this module exists for. Admins are exempted at `:390-391`
(`if self.env.is_admin(): extra_checks = False`), so it does not bite an administrator, but a
non-admin staff member cannot merge two contacts into one and keep both addresses.

This is left alone deliberately. Relaxing it means forcing `extra_checks=False`, which would also
pre-disable any future check Odoo puts behind that flag. Revisit when someone other than an
administrator actually needs to do contact cleanup.

### Deliberate non-goals

Each of these keeps reading the primary address only:

- **Sending.** An additional address means "we also know them here", never "mail them here".
  `email_formatted` is untouched.
- **Blacklist.** `mail.blacklist` keys on an address string and is consulted only by mass mailing
  and SMS — `mail/models/mail_mail.py` never checks it, so transactional mail is unaffected either
  way. An additional address could be blacklisted while `partner.is_blacklisted` still reads false.
  Revisit if we ever send marketing mail, where GDPR obliges honouring opt-outs.
- **Bounce counters and mail-loop detection**, which query `email_normalized` with raw domains
  (`mail/models/mail_thread.py:776, 917, 978, 1697, 2028, 2035`).

### CRM, Recruitment, and Helpdesk

Three apps keep a record's email and its contact's email in step, and without help each would
overwrite a contact's primary address with an additional one:

| App         | Edition    | The sync                                                                         |
| ----------- | ---------- | -------------------------------------------------------------------------------- |
| CRM         | Community  | `crm.lead._inverse_email_from`, decided by `_get_partner_email_update`           |
| Recruitment | Community  | `hr.candidate._inverse_partner_email`, which decides inline                      |
| Helpdesk    | Enterprise | `helpdesk.ticket._inverse_partner_email`, decided by `_get_partner_email_update` |

**Recruitment's patch target is 18-specific.** On 19 an applicant's own `email_from`,
`partner_phone`, and `name` decide the sync inline, in `hr.applicant._inverse_partner_email`. On 18
those fields are `related` to a separate `hr.candidate` record
(`hr_recruitment/models/hr_applicant.py:43-51`) — 19 merged the two models back into one — and it is
`hr.candidate._inverse_partner_email` (`hr_recruitment/models/hr_candidate.py:112-132`) that
actually writes the contact's email. The applicant model still exists and still works the same way
from a user's chair; only the class carrying the method this module patches moved.

When the record's email differs from the contact's, the record's is written onto the contact. In
core the two only differ when someone edits one of them, because core matches mail on the primary
address alone. This module also matches on additional addresses, so a lead created from one arrives
with an email that differs from its contact's primary, and the sync then replaces the primary with
it. Found on 25 September 2026, when a lead emailed from a demo contact's additional address
replaced the contact's primary address.

**None of the three is a dependency, so the fix is a patch, not an `_inherit`.** A bridge module per
app would be the conventional answer: three modules, one of them Enterprise-only and so unable to
live in this repo. Instead `res.partner._register_hook` calls `email_sync.install()`, which patches
the sync of whichever of the three apps is installed onto its registry class, the way
`base_automation` patches models for its rules (`base_automation/models/base_automation.py`,
`_register_hook`). Every registry load builds fresh classes and runs the hook again, so an app
installed later is covered, and uninstalling leaves nothing to undo. The module names Helpdesk's
model and method, but it neither depends on Helpdesk nor contains any of its code, so it still
installs on Community.

- **CRM and Helpdesk** decide the sync in `_get_partner_email_update`, which the patch answers
  `False` when the record's email is one of the contact's additional addresses. The same answer
  drives the form's warning that the contact's email will be updated, so both stop together.
- **Recruitment** decides inline, in a loop that also syncs the name and phone, so its inverse runs
  under the `vmk_keep_primary_email` context flag instead. Under that flag `res.partner.write` drops
  an email that is one of that contact's own additional addresses, and writes the rest as asked.

Outside those syncs nothing changes: a record with a genuinely new address still updates its
contact, and typing an additional address into the contact's email field still makes it primary.

**Patches break quietly**, so re-check them on every major upgrade. If Odoo renames one of these
methods, `install()` logs a warning naming it, and `test_every_installed_app_is_patched` fails on a
database that has the app.

### Translations

`i18n/` carries the template and Spanish and Catalan catalogues; Odoo loads `i18n/*.po` on install
with no manifest entry. Terms this module shares with core — _Contact_, _Created by_, _Send Email_ —
reuse core's own wording in each language rather than a second translation of the same word, so the
module reads as part of the backend.

Regenerating the template after changing any user-facing string. Odoo 18 has no `i18n export`
subcommand — that arrived later — so the flag is `--i18n-export` on the ordinary server command:

```bash
# Run from the directory holding your Compose file; REPO is the path to this repo.
REPO=/path/to/odoo-addons
docker compose run --rm -e PGHOST=db -e PGUSER=odoo -e PGPASSWORD=odoo \
    -v "$REPO/vmk_partner_email_multiple/i18n:/mnt/out" --entrypoint odoo odoo \
    -d test --i18n-export=/mnt/out/vmk_partner_email_multiple.pot \
    --modules=vmk_partner_email_multiple --stop-after-init
```

Two details are doing work in that command. `--entrypoint odoo` is required because the image's
entrypoint translates `HOST`/`USER`/`PASSWORD` into `--db_host` and friends, which `--i18n-export`
rejects outright — hence passing the connection as libpq's `PG*` variables instead. And the output
path is required because the export otherwise writes into each module's own `i18n/` folder, which
the harness mounts read-only.

Upgrade the module with the database's language loaded to see a change take effect; `-u` alone
reloads the `.po` but the terms only render for a user whose language is set.

**The module's own name and summary are a separate, hand-maintained exception.** They live on
`ir.module.module` records that belong to `base`'s xmlid namespace, so the export above never sees
them — they are written into the POT and both catalogues by hand and re-running the export would
silently drop them. See
[`vmk_language_systray`'s README](../vmk_language_systray#the-modules-own-name-and-summary-are-hand-maintained-in-i18n)
for the full explanation; `tests/test_model.py::TestModuleNameTranslation` guards it here.

### Testing

Against a local Odoo 18 with this repo on the addons path — Postgres, the `odoo:18.0` image, and the
repo root mounted at `/mnt/extra-addons`:

```bash
docker compose run --rm odoo odoo -d test --init vmk_partner_email_multiple \
    --without-demo=all --stop-after-init
docker compose run --rm odoo odoo -d test -u vmk_partner_email_multiple \
    --test-enable --test-tags /vmk_partner_email_multiple --stop-after-init
```

`-u` on a module that is not installed does nothing and reports nothing, so install first and check
`ir_module_module.state` rather than trusting a clean log.

`tests/test_email_sync.py` skips each app's tests where the app is missing, so run it on a database
that also has `crm` and `hr_recruitment` installed, plus `helpdesk` where Enterprise is available.
Core's own suites for all three pass with this module installed.

Valencia Makers also runs these on a shared harness of its own; it is not needed to run the tests
above.

### License

**LGPL-3**, as the whole repo is. See `LICENSE`, which carries the LGPL-3 text followed by the GPL-3
it incorporates by reference.

This module was the first reason the repo came to prefer LGPL: **other modules should be able to
build on it.** Several addresses per contact is a gap in Odoo itself, and nothing free fills it — so
anything that wants to work with contact email is likely to want this underneath rather than to
reimplement it. AGPL would force every such module to be AGPL too, including commercial ones, which
would push authors back towards reinventing it badly.

LGPL keeps both halves. A module may `depends` on this one under any licence it likes, proprietary
included, because that is a work that _uses_ the library. But modifying and redistributing **this**
module still obliges the modified version to be LGPL with source — so the case the default was
chosen to prevent, someone shipping a closed copy of this code as their own product, is prevented
here too.

The OCA makes the same distinction, using LGPL-3 where modules are expected to be extended.
`web_chatter_position` from `OCA/web`, vendored in `../Odoo Addons - External`, is one of theirs
under LGPL-3 for this reason.
