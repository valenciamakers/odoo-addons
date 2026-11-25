Switch off Odoo's website visitor tracking, per website.

In standard Odoo, the **Website** app records every visitor and each page they view, under
**Website › Reporting › Visitors**: an id made from their IP address, browser, and session, the
country Odoo looks up from the IP address, their language and time zone, and each tracked page with
its time. There is no setting to stop it, and the cookies bar doesn't either. This module switches
it off on every website the moment it is installed, and adds a **Track Visitors** setting to turn it
back on for any website that wants it.

**Installation**

Install **Disable Visitor Tracking** from the Apps menu. It only requires Odoo's **Website** app.

There is nothing to configure: tracking is off on every website, the ones you already have and any
you make afterwards.

**Using it**

- **To track visitors on a website again**, open **Website › Configuration › Settings**, choose the
  website at the top, and tick **Track Visitors**, under **Tracking & SEO**, beside the cookies
  bar. That website then records visitors as Odoo does without this module.
- **Off, the website records no visitors at all**: no page views, and no visitor linked to what a
  form creates, such as a CRM lead or an event registration, which are made without one.
- **Visitors already recorded stay** until you delete them, in **Website › Reporting › Visitors**.
  Deleting a visitor deletes its page views.
- **Uninstalling the module** puts Odoo's own behavior back, with tracking on everywhere.

**Limits**

- **Analytics you add yourself**, such as Google Analytics or Plausible, are separate settings, and
  are not affected.
- **Two features need a visitor**, so leave **Track Visitors** on for a website that uses them:

  - **Push notifications**, from Enterprise's **Social Marketing**: with tracking off, a browser
    subscribing to them gets an error, and nothing is recorded.
  - **A visitor's favorite talks and reminders** on an event's agenda, from **Advanced Events**: with
    tracking off, visitors who are not signed in would share one list. Signed-in users are not
    affected.

- **A visitor is no longer linked to their account** when they sign in, since none is recorded
  before.

**Languages**

English, Spanish, and Catalan. If any translation seems incorrect, please
`contact us <mailto:info@valenciamakers.es>`_ and we will fix it.

**Changelog**

*20.0.1.0.0 (25 November 2026)*

- First release.
