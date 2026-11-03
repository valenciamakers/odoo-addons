# To do — `vmk_website_disable_tracking`

What is still ahead before the module's store listing is published. How it works now is in
`README.md`.

## Bridges for the two modules that need a visitor

_Added 3 November 2026. Not needed for our own site, which runs neither module; needed before the
listing is published._

With tracking off, `ir.http._get_visitor_from_request` returns no visitor, even when a caller asks
with `force_create=True`. Two modules are written on the assumption that it always returns one, so
each needs a small auto-installed bridge module (`auto_install: True`, depending on this module and
that one) that switches its visitor feature off while tracking is off on the website.

- **Enterprise `social_push_notifications`** asks for a visitor with `force_create=True` when a
  browser subscribes to push (`controllers/main.py`), and stores it in
  `website.visitor.push.subscription.website_visitor_id`, a required field. With tracking off,
  subscribing fails with a database error. The bridge should stop the site offering push
  subscriptions while tracking is off, for example by treating `website.enable_push_notifications`
  as off, and say so beside the setting. **It depends on Enterprise, so it goes in the Private repo,
  not here**: this repo's modules work on Community.
- **Community `website_event_track`** keeps a public user's wishlisted and reminded talks in
  `event.track.visitor` against their visitor (`_get_event_track_visitors` in
  `models/event_track.py`). With no visitor, the search is for `visitor_id = False`, so every
  anonymous visitor matches the rows every other one made, and new rows are made with no visitor:
  they share one wishlist and one set of reminders. The bridge should hide the wishlist and reminder
  buttons from public users while tracking is off, and refuse the routes behind them, leaving them
  to logged-in users, whose rows are kept against their partner.

Each bridge needs its own tests, run on a database with only its declared dependencies, and its own
README; this module's README then points at them instead of telling the reader to leave tracking on.
