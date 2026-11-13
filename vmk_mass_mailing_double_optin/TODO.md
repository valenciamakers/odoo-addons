# To do — `vmk_mass_mailing_double_optin`

What is still ahead before the module's store listing is published. How it works now is in
`README.md`.

## Store page

_Added 13 November 2026._

The page, `static/description/index.html`, its screenshots (a recipe in `tools/shots/recipes/`), and
the cover (`tools/covers/`), once the wording and the backend have been reviewed, so the screenshots
are taken once. The icon is done.

## The other nineteen languages

_Added 13 November 2026._

`odev i18n fill` gave each language core's translations of the shared terms, leaving about thirty of
our own strings blank in each, which show in English. They go through the usual two agents and
`--memory`, after the wording review, so they are translated once.

## Signing up again while awaiting confirmation

_Added 13 November 2026. A question, not a design._

Core's newsletter block writes nothing when the address already has a subscription that is not opted
out (`website_mass_mailing`, `subscribe_to_newsletter`), so someone who lost the email and signs up
again gets no new link until the first expires. Fixing it means reacting to a signup that changes no
record, which only a bridge module on `website_mass_mailing` could see. Worth it only if people turn
out to hit it.
