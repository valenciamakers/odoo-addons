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

        Patching the empties after ``super()`` is enough, and cannot resurrect a
        partner core deliberately excluded: an address banned as an alias, or
        filtered out by ``filter_found``, is rejected by the resolver too.
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

        resolved = self.env["vmk.partner.email"]._resolve_partners(
            [normalized for _index, normalized in pending]
        )
        for index, normalized in pending:
            if normalized in resolved:
                results[index] = resolved[normalized]
        return results
