# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import models
from odoo.osv import expression
from odoo.tools import email_normalize


class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    def _mail_find_partner_from_emails(
        self, emails, records=None, force_create=False, extra_domain=False
    ):
        """Resolve additional addresses ourselves, before core's own search runs.

        On 18 this method does not delegate to ``_find_or_create_from_emails``,
        as it does on 19: it searches followers, users, then partners by a plain
        ``email_normalized`` domain (``mail_thread.py:1986-1990``). And its final
        step (``:2108-2116``) re-matches every candidate by the partner's *own*
        ``email_normalized``, so a partner found by an additional address is
        dropped on the way out, and with ``force_create=True`` a duplicate
        contact is created in its place. Patching the result afterwards cannot
        undo that. So the addresses this module can resolve are resolved here,
        within ``extra_domain``, and only the rest go to ``super()``. An address
        a primary holder owns is never resolved here, so core's own tie-break
        still decides those.
        """
        normalized_inputs = [email_normalize(email, strict=False) for email in emails]
        resolved = self.env["vmk.partner.email"]._resolve_partners(
            [normalized for normalized in normalized_inputs if normalized]
        )
        if extra_domain and resolved:
            # Reproduce core's own domain, which it ANDs onto each internal search,
            # rather than handing back a partner that domain would have excluded.
            visible_ids = set(
                self.env["res.partner"]
                .search(
                    expression.AND(
                        [[("id", "in", [partner.id for partner in resolved.values()])], extra_domain]
                    )
                )
                .ids
            )
            resolved = {
                normalized: partner
                for normalized, partner in resolved.items()
                if partner.id in visible_ids
            }
        if not resolved:
            return super()._mail_find_partner_from_emails(
                emails, records=records, force_create=force_create, extra_domain=extra_domain
            )

        remaining = [
            email
            for normalized, email in zip(normalized_inputs, emails)
            if normalized not in resolved
        ]
        fallback = (
            super()._mail_find_partner_from_emails(
                remaining, records=records, force_create=force_create, extra_domain=extra_domain
            )
            if remaining
            else []
        )
        fallback = iter(fallback)
        return [
            resolved[normalized] if normalized in resolved else next(fallback)
            for normalized in normalized_inputs
        ]
