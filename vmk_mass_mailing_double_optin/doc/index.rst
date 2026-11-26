Require confirmation on new mailing list subscriptions, and log every consent change.

In standard Odoo, any email address typed into a website's newsletter form is subscribed
immediately, regardless of who entered it. This module sends each new subscriber an email with a
confirmation link, and sends them no mailings from that list until they have confirmed. A consent
log records every subscription, confirmation, unsubscription, and blacklisting, with the date and
where it came from.

**Installation**

Install **Double Opt-In for Email Marketing** from the Apps menu. It only requires Odoo's **Email Marketing** app, and works on both Community and Enterprise.

**Using it**

Double opt-in is on for every mailing list once the module is installed, the lists you already have
included. Contacts already subscribed are not affected, and no one is sent a confirmation email
until someone next subscribes.

- **Switch it off for a list** with **Double Opt-In Confirmation** on the mailing list's form,
  beside **Show In Preferences**.
- **Signing up on the website**, through the newsletter block, a newsletter form, or the
  newsletter box at checkout, sends a confirmation email. Until the person confirms, the
  subscription shows **Awaiting Confirmation** on the contact's **Subscriptions** tab, and mailings
  to that list leave them out, listed as opted out in the mailing's statistics.
- **Opening the link** shows a page with a **Confirm Subscription** button, and the user must
  click it to confirm. Mail security filters open the links in an email to check them, and would
  otherwise confirm on the reader's behalf.
- **Links expire after seven days.** Subscriptions still unconfirmed then are removed, and so is a
  contact the website created for that signup alone.
- **Resend Confirmation**, on a subscription awaiting it, sends a new link and stops the old one
  working. **Request Confirmation**, on any other subscription, asks someone already subscribed to
  confirm; they receive no mailings from that list until they do.
- **Contacts you add or import yourself** are subscribed immediately, as in standard Odoo, and the
  log records who added the contact.
- **To ask many contacts to confirm at once**, after an import for example, open the list's
  **Recipients**, select the contacts, and click **Request Confirmation**. Choose the mailing lists
  and the email's language, and the dialog says how many emails it will send. Contacts already
  confirmed, awaiting confirmation, unsubscribed, blacklisted, or without an email address are
  skipped.
  The language is for contacts whose own is not known: someone who signed up on the website gets
  the email in the language they used there.
- **Changing preferences from a mailing's link** does not require confirmation, since
  confirmation is assumed because they are responding to an email.

**The consent log**

Open it from **Email Marketing › Reporting › Consent Log**, or from the **Consent Log** button on a
mailing contact. Each line has the date, the email address, the mailing list, what happened, and
where from: the website, a link in an email, an internal user, an import, or Odoo itself. For a
change made on the website, it also has the visitor's IP address, browser, and page.

Lines cannot be edited by anyone. Email Marketing users can read them, and only Settings
administrators can delete them, for example to answer a request to erase someone's data. Lines stay
when a contact or a list is deleted.

**Limits**

- **Signing up again while awaiting confirmation sends nothing new**, because Odoo finds the
  subscription already there. Use **Resend Confirmation**, or the person can sign up again once the
  link has expired.
- **Subscriptions by phone number**, with SMS Marketing, have no email address to confirm, and are
  subscribed at once.
- **The email and the pages** are in the language the person used on the website, or for a request
  from the backend, the language chosen in the dialog, else yours. Edit the email
  under **Settings › Technical › Email › Email Templates**, in developer mode: *Email Marketing:
  Confirm Subscription*.

**Languages**

English, Spanish, and Catalan. If any translation seems incorrect, please
`contact us <mailto:info@valenciamakers.es>`_ and we will fix it.

**Changelog**

*18.0.1.0.0 (26 November 2026)*

- First release.
