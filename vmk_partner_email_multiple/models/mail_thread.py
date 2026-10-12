# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import models
from odoo.tools import email_normalize


class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    def _mail_find_partner_from_emails(
        self, emails, records=None, force_create=False, extra_domain=False
    ):
        """Repair the resolution step, which repeats core's filter independently.

        The *search* half needs nothing here: in 19 this method delegates to
        ``_partner_find_from_emails`` (mail_thread.py:2156-2165), which funnels
        everything through ``res.partner._find_or_create_from_emails`` at :2094 --
        already overridden. What it then does on its own is resolve each input back
        to a partner by ``p.email_normalized == email_key or p.email == email_key``
        (:2173), which no additional address can satisfy. So the right partner is
        found, ends up in ``all_partners``, and is dropped on the way out.

        Patching the empties after ``super()`` is enough, but the resolver does not
        know what core banned on the way in. ``_partner_find_from_emails`` builds a
        ban list with ``mail.alias.domain._find_aliases`` (bounce, catchall and
        default-from addresses, and mail aliases) and hands it to
        ``_find_or_create_from_emails`` as ``ban_emails``; an empty slot left by
        that ban looks exactly like an address nobody holds. So the same list is
        built here for the pending addresses and passed on, or an alias held as an
        additional address would resolve to its holder after all.
        """
        results = super()._mail_find_partner_from_emails(
            emails, records=records, force_create=force_create, extra_domain=extra_domain
        )
        pending = []
        for index, (email_input, partner) in enumerate(zip(emails, results)):
            if partner:
                continue
            normalized = email_normalize(email_input)
            if normalized:
                pending.append((index, normalized))
        if not pending:
            return results

        pending_emails = [normalized for _index, normalized in pending]
        # Core's own ban list, as _partner_find_from_emails builds it (avoid_alias).
        alias_emails = self.env["mail.alias.domain"].sudo()._find_aliases(pending_emails)
        resolved = self.env["vmk.partner.email"]._resolve_partners(
            pending_emails, ban_emails=alias_emails
        )
        for index, normalized in pending:
            if normalized in resolved:
                results[index] = resolved[normalized]
        return results
