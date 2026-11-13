# Double Opt-In for Email Marketing (`vmk_mass_mailing_double_optin`)

Confirm new mailing list subscribers by email, and log every consent change. Someone who subscribes
on the website receives an email with a confirmation link, and receives no mailings from that list
until they confirm. A consent log records every subscription, confirmation, unsubscription, and
blacklisting, with the date, the page, the IP address, and the browser of whoever made it.

**How to use it** is in the user documentation, [`doc/index.rst`](doc/index.rst), which the Odoo
Apps Store also shows on the module's page, together with the changelog.

It depends only on `mass_mailing` (_Email Marketing_), and works on Community and Enterprise alike.
LGPL-3, © 2026 Valencia Makers, SL. Not yet released: its store page, cover, and screenshots are
still to come (`TODO.md`).

## For developers

What follows is how the module works and why it is built this way: what core does, which of its
methods this relies on, and the traps found on the way.

### Where the state lives

On Odoo 20 a mailing contact joins a list through `mailing.subscription`, one row per contact and
list, whose `opt_out` says whether they left it. Consent is per list, so the confirmation state is
on that row too: `vmk_confirmation_state` is empty (no confirmation was asked for), `pending`, or
`confirmed`. Core's own meaning of every field is untouched. In particular a subscription awaiting
confirmation is **not** stored as opted out, which would give it an unsubscription date and count it
in the list's opt-out statistics.

### Who has to confirm

A subscription needs confirmation when it begins, or begins again after an unsubscription, on a list
with **Double Opt-In** on (`mailing.list.vmk_double_optin`, default on), for a contact with an email
address, **made by a user who is not internal**. That one rule, in
`mailing.subscription._vmk_needing_confirmation`, covers every website path core has, and any a
third-party module adds, without overriding a single controller:

- `website_mass_mailing`'s newsletter block (`subscribe_to_newsletter`), its form builder
  (`WebsiteNewsletterForm.insert_record`), and `website_sale_mass_mailing`'s checkout checkbox all
  write through `request.env[...].sudo()`. **`sudo()` keeps the uid**, so `env.user` is still the
  public or portal user, and `_is_internal()` is false.
- Users adding contacts in the backend, imports (`import_file` in the context), and scheduled
  actions are internal and vouch for the contact, as in core.
- **Core's "manage your subscriptions" page**, `/mailing/list/update`, is the one public path that
  needs no confirmation when it carries a `hash_token`: core refuses it unless the token is the
  mailing's HMAC for that address, so only someone reading the address has it. `controllers/main.py`
  sets `CONTEXT_PROVEN` around core's method for that case. Without a token the visitor is a
  signed-in user managing their own account's address, which nothing has proven.

Subscriptions arrive by three ORM routes, and each is hooked:

- `mailing.subscription.create`, and `write` on `opt_out` for a re-subscription.
- **`mailing.contact.list_ids`, a many2many over `mailing_subscription`'s own table.** The ORM
  inserts and deletes those rows itself, without calling the subscription's `create` or `unlink`, so
  `mailing.contact.create` and `write` find the new rows afterwards and treat them as created. The
  form builder creates contacts this way.
- Deleting a contact or a list deletes its subscriptions by `ON DELETE CASCADE` in the database,
  again without `unlink`, so both models log them first.

Each route records the subscription ids it has handled in `cr.cache` (`SEEN_CREATED`,
`SEEN_REMOVED`), which lives as long as the transaction, so a subscription reached by two routes in
one write is logged once.

### Keeping them out of mailings

Core decides who is opted out of a list mailing in `mailing.list._mailing_get_opt_out_list`, through
`mailing.mailing._get_opt_out_list`, and cancels their mail with the failure type `mail_optout`.
This module adds the addresses awaiting confirmation to that set, keeping core's rule that an
address still subscribed to another of the mailing's lists receives the mailing. Core's set counts a
subscription awaiting confirmation as subscribed, so the override adds to core's result rather than
replacing it. A pending contact is still counted among a mailing's recipients beforehand, exactly as
an opted-out one is.

### The link

`_vmk_confirmation_token` is `tools.hmac` over the subscription's id, the contact's normalized
address, and the time the confirmation was requested, the technique core uses for its own
unsubscription links. **Nothing is stored**: the token is computed again to check it, a new request
changes the time and so invalidates the previous link, and changing the contact's address
invalidates it too. The URL reaches the email template through the rendering context (`ctx`) rather
than a field, because a field would let any email marketing user read a working link and confirm on
someone's behalf. A link is valid for seven days (`CONFIRMATION_VALIDITY`); the email says so in
words, so that constant and the template's wording change together.

**Opening the link confirms nothing.** Mail security gateways open the links in an email to scan
them, so a link that confirmed on a GET would confirm subscriptions nobody asked for, and the log
would hold the scanner's IP address as proof. The GET shows a page with a button, and only its POST
confirms, with core's CSRF check. Core's own unsubscription page asks for a click the same way, and
ours uses its layout, `mass_mailing.layout`. A wrong token, a subscription that does not exist, an
expired link, and an unsubscribed address all get the same page, so the route reveals nothing.

A second request within ten minutes (`RESEND_INTERVAL`) sends no new email, and the first link keeps
working. Core's website already writes nothing for an address subscribed or awaiting confirmation,
so this only matters for an unsubscribe and re-subscribe in quick succession. The backend's **Resend
Confirmation** button always sends.

The email is `mail_template_confirmation`, on `mailing.subscription`, wrapped in core's
`mail.mail_notification_light`. It goes out in the language the visitor used on the website
(`vmk_confirmation_lang`), through the mail queue, which the module wakes rather than sending inside
the visitor's request. With the Website app, the link points at the domain configured for the
website the visitor signed up on (`website.get_base_url()`), so a database serving two websites
links each visitor back to theirs. It never takes the request's `Host` header, which the visitor
controls, and which would let anyone have our email link to a site of their choosing.

### Expiry

`ir_cron_expire_confirmations` deletes, daily, the subscriptions whose link expired unconfirmed,
logging each as **Expired**. A contact the website created for that signup alone (no other
subscription, created by a user who is not internal) is deleted with it. Data nobody consented to
keeping should not be kept, and the consent log still holds a line for what was asked and when.

### The consent log

`vmk.mailing.consent.log` has one line per change, written only by `_vmk_log` as superuser. Nobody
holds a create or write permission on it, and its `write` refuses even the superuser. Settings
administrators alone may delete a line, to answer an erasure request. Each line copies the address
and the list's name, so it still says what it recorded after the contact or the list is deleted: its
many2ones are `ondelete="set null"`, which the database applies without the ORM.

The **source** is read from the environment, in `_vmk_source`: Imported, then Email Link (the proven
context, set by our confirmation route and core's subscription page), Website (a user who is not
internal), System (the superuser: scheduled actions and `odoo shell`), and otherwise Internal User.
For a request, the line keeps the IP address, the user agent, and the page: the referrer for a JSON
call, such as a newsletter form, and the requested URL otherwise, both **without their query
string**, which on core's pages holds the address and a mailing token.

Blacklisting is logged as well, from `mail.blacklist`, because it stops every mailing to an address
at once. Core unblacklists by archiving the entry, and `create` returns the existing entry for an
address it already has, so both are told apart from a real change.

What is not logged: bounces, which change no one's consent, and an unsubscription reason given
before an unsubscription, which core never does.

### Core's tests

`mass_mailing`'s suite passes beside ours except for seven query counts in
`test_mailing_contact_to_list` (`_from_partners` and its wizard), which find one or two queries more
than core allows: the consent log's insert, and on a `list_ids` write the subscriptions read before
and after. Logging every subscription costs that by design. Checked on Enterprise and Community, 13
November 2026.

### Translations

Spanish and Catalan follow core's register for these pages and emails, which address the reader as
_usted_ and _vós_, as core's own unsubscription pages do. "Double opt-in" is _doble confirmación_
and _doble confirmació_.
