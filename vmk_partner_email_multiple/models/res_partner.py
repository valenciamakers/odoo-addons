# Copyright 2026 Valencia Makers, SL
# License MIT (https://opensource.org/licenses/MIT).

from odoo import api, fields, models, tools
from odoo.fields import Domain
from odoo.tools import email_normalize


class ResPartner(models.Model):
    _inherit = "res.partner"

    vmk_email_ids = fields.One2many(
        "vmk.partner.email",
        "partner_id",
        string="Additional Emails",
        help="Other addresses this contact writes from. Mail arriving from any of "
        "them is matched to this contact. Nothing is ever sent to them.",
    )

    # ------------------------------------------------------------
    # Matching
    # ------------------------------------------------------------

    @api.model
    def _find_or_create_from_emails(
        self,
        emails,
        ban_emails=None,
        filter_found=None,
        additional_values=None,
        no_create=False,
        sort_key=None,
        sort_reverse=True,
    ):
        """Match additional addresses before core gets a chance to create duplicates.

        Widening core's search domain is not enough and this is the trap that makes
        the module non-trivial. ``mail/models/res_partner.py`` searches
        ``[('email_normalized', 'in', [...])]`` at :175, but then resolves each input
        address back to a partner at :222-232 by comparing
        ``partner.email_normalized == email_normalized``. Satisfy the domain through
        this module's child table and that final step still hands back an empty
        recordset.

        So rather than reimplement the method with both halves widened -- which would
        also mean copying LGPL source into an MIT module -- resolve the addresses we
        can here, pass only the rest to ``super()``, and splice the two result lists
        back into input order. Per-email resolution cannot cross-contaminate, because
        core matches each input against its own normalized value.
        """
        name_emails = [tools.parse_contact_from_email(email) for email in emails]
        resolved = self.env["vmk.partner.email"]._resolve_partners(
            [normalized for _name, normalized in name_emails],
            ban_emails=ban_emails,
            filter_found=filter_found,
            sort_key=sort_key,
            sort_reverse=sort_reverse,
        )
        if not resolved:
            return super()._find_or_create_from_emails(
                emails,
                ban_emails=ban_emails,
                filter_found=filter_found,
                additional_values=additional_values,
                no_create=no_create,
                sort_key=sort_key,
                sort_reverse=sort_reverse,
            )

        remaining = [
            email
            for (_name, normalized), email in zip(name_emails, emails)
            if normalized not in resolved
        ]
        fallback = (
            super()._find_or_create_from_emails(
                remaining,
                ban_emails=ban_emails,
                filter_found=filter_found,
                additional_values=additional_values,
                no_create=no_create,
                sort_key=sort_key,
                sort_reverse=sort_reverse,
            )
            if remaining
            else []
        )
        fallback = iter(fallback)
        return [
            resolved[normalized] if normalized in resolved else next(fallback)
            for _name, normalized in name_emails
        ]

    @api.model
    def find_or_create(self, email, assert_valid_email=False):
        """Legacy single-address path, which searches separately (:96-107)."""
        if email:
            _parsed_name, parsed_email_normalized = tools.parse_contact_from_email(email)
            if parsed_email_normalized:
                resolved = self.env["vmk.partner.email"]._resolve_partners(
                    [parsed_email_normalized]
                )
                if parsed_email_normalized in resolved:
                    return resolved[parsed_email_normalized]
        return super().find_or_create(email, assert_valid_email=assert_valid_email)

    # ------------------------------------------------------------
    # Search
    # ------------------------------------------------------------

    @api.model
    def _search_display_name(self, operator, value):
        """Let the contacts autocomplete find additional addresses too.

        ``_rec_names_search`` (base/models/res_partner.py:189) does accept dotted
        paths -- ``orm/models.py:1462-1473`` resolves the last field in the chain --
        so ``vmk_email_ids.email`` would work as an entry. But appending to a class
        attribute means restating core's whole list and silently losing whatever
        Odoo adds to it later, so combine the domains instead. The aggregator
        follows core's own choice at :1460.
        """
        domain = super()._search_display_name(operator, value)
        if not operator.endswith("like") or not value or not isinstance(value, str):
            return domain
        extra = Domain("vmk_email_ids.email", operator, value)
        if operator in Domain.NEGATIVE_OPERATORS:
            return domain & extra
        return domain | extra

    # ------------------------------------------------------------
    # Merge
    # ------------------------------------------------------------

    def _vmk_absorb_emails(self, emails):
        """Keep ``emails`` as additional addresses, skipping any already held.

        Called by the merge wizard. Addresses that cannot be normalized are kept
        too: they will never match anything, but the alternative is destroying a
        contact's address during a merge, and core itself stores unparseable
        addresses deliberately so a typo can be corrected later
        (mail/models/res_partner.py:130-132).
        """
        self.ensure_one()
        # _update_foreign_keys moved the source contacts' rows here in raw SQL,
        # which the cache does not see.
        self.invalidate_recordset(["vmk_email_ids"])

        known = set(self.vmk_email_ids.mapped("email_normalized"))
        known.add(self.email_normalized)
        known.discard(False)

        to_create = []
        for email in emails:
            key = email_normalize(email, strict=False) or (email or "").strip().lower()
            if not key or key in known:
                continue
            known.add(key)
            to_create.append({"partner_id": self.id, "email": email})
        if to_create:
            self.env["vmk.partner.email"].create(to_create)
        return self.vmk_email_ids
