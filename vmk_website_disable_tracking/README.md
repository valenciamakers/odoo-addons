# Disable Visitor Tracking (`vmk_website_disable_tracking`)

Switch off Odoo's website visitor tracking, per website. Odoo's Website app records every visitor
and the pages they view by default, under Website › Reporting › Visitors. This module turns that off
on every website the moment it is installed, and adds a **Track Visitors** setting to turn it back
on for any website that wants it.

It depends only on `website`. LGPL-3, © 2026 Valencia Makers, SL.

## How to use it

Install **Disable Visitor Tracking** from the Apps menu. There is nothing to configure: tracking is
off on every website, the ones you already have and any you make afterwards.

- **Website › Configuration › Settings › Track Visitors**, under Tracking & SEO beside the cookies
  bar, for the website chosen at the top of the page. Tick it to record visitors on that website
  again, as Odoo does without this module.
- **Off, the website records no visitors at all**: no page views, and no visitor linked to what a
  form creates, such as a CRM lead or an event registration, which are made without one.
- **Visitors already recorded stay** until deleted, in Website › Reporting › Visitors. Deleting a
  visitor deletes its page views.
- **Uninstalling the module** puts Odoo's own behaviour back, with tracking on everywhere.

## For developers

### What Odoo tracks

Website records a visitor for each browser that views a tracked page, under an id hashed from the IP
address, the browser's user agent, and the `session_id` cookie (`website_visitor.py`,
`_get_access_token`), with the country Odoo looks up from the IP address, the language, and the time
zone. Each view of a tracked page adds a page view, with its URL and time.

A page is tracked when `website._is_tracking_enabled` says so: a news article, an event, or any
record shown as a page is always tracked, and a website page when its Track setting is on, which
website turns on for every page created in the editor. The page then carries
`data-tracking-enabled`, and website's tracker calls `/website/odoo_track` three seconds after the
page loads. Forms add visitors of their own: website_crm links each lead to one, and website_event
each registration, creating one if needed. The cookies bar does not stop any of this.

### How it is switched off

Two overrides, both reading `website.vmk_track_visitors`:

- **`website._is_tracking_enabled`** returns False, so no page carries the mark and the browser
  never reports a view.
- **`ir.http._get_visitor_from_request`** returns an empty visitor, before website looks one up or
  creates one. Every visitor Odoo records is made there (`_upsert_visitor` has no other caller), by
  the tracker's route and by the forms, so this closes the route to a call made by hand, and every
  other way in. Existing visitors are not looked up either, so none is updated, and a visitor is not
  merged with a user's when they log in.

**Why an empty recordset is safe.** It is what website itself returns when it finds no visitor, so a
caller written for a visitor that does not exist yet already handles it: a lead or a registration is
made without one, and `visitor.partner_id` of nothing is nothing. Core's own callers were read
against it on 2 November 2026. Two interactions are worth knowing, both with modules that exist to
serve visitors:

- **Enterprise `social_push_notifications`** stores a push subscription against a visitor, which it
  asks for with `force_create=True` and which is a required field. With tracking off, subscribing
  fails with a database error instead of recording anything.
- **Community `website_event_track`** keeps a public user's wishlisted and reminded tracks against
  their visitor. With none, `_get_event_track_visitors` searches for a visitor of `False`, so
  anonymous visitors would share one set of rows. Leave Track Visitors on for a website whose
  visitors use those features. A bridge module for each, switching the feature off while tracking is
  off, is planned in `TODO.md`.

### The setting, and what installing does

`website.vmk_track_visitors` is a `Boolean` that **defaults to False**, so a website made after
install is off. On install, Odoo adds the column to the websites that already exist and fills it
with the default (`_init_column_data` in `odoo/orm/fields.py`). A boolean default of False is stored
as NULL there, which Odoo reads back as False, so an existing website is off with no
`post_init_hook` and no write. The settings form edits it through the related field
`res.config.settings.website_vmk_track_visitors`, for the website chosen at the top.

Installing does not lock the setting: Track Visitors ticked on a website stays ticked through an
upgrade of the module, since Odoo fills the default in only when it adds the column.

### Translations

The module's own name and summary are `ir.module.module` records whose xmlid belongs to `base`
(`base.module_vmk_website_disable_tracking`). Odoo 20's `i18n export` writes them into the
catalogue, beside a `description` entry holding this whole README, which we leave out: nothing
displays it. `tests/test_translations.py` fails if the POT loses either entry, which would otherwise
leave the name in English in a translated database without a word. The rest of the catalogue is the
setting's label and help, and four model and field names that core already translates, taken in
core's wording.

### Testing

```bash
odoo -d <db> -u vmk_website_disable_tracking --test-enable --test-tags /vmk_website_disable_tracking --stop-after-init
```

`tests/test_tracking.py` checks a page made as the editor makes one. Right after install, the
website has tracking off, and so does a website made afterwards. With it off, the page carries no
mark, a view reported by hand records no visitor, and a form asking with `force_create` gets none.
With Track Visitors ticked, the page carries the mark, a reported view records a visitor, and a form
gets one.
