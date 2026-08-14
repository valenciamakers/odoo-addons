# Copyright 2026 Valencia Makers, SL
# License MIT (https://opensource.org/licenses/MIT).

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import email_normalize


class VmkPartnerEmail(models.Model):
    """An *additional* email address for a contact.

    Deliberately a child table rather than a redefinition of ``res.partner.email``:
    the primary address keeps its core meaning and this module never writes to it
    on its own initiative, so uninstalling leaves every contact intact.
    """

    _name = "vmk.partner.email"
    _description = "Additional Contact Email"
    _order = "sequence, id"
    _rec_name = "email"

    partner_id = fields.Many2one(
        "res.partner",
        string="Contact",
        required=True,
        ondelete="cascade",
        index=True,
    )
    email = fields.Char(string="Email Address", required=True)
    email_normalized = fields.Char(
        string="Normalized Email",
        compute="_compute_email_normalized",
        compute_sudo=True,
        store=True,
        index=True,
        help="Lower-cased address without a display name, used for matching. "
        "Mirrors res.partner.email_normalized.",
    )
    label = fields.Char(
        string="Label",
        help="Free-text note about this address, e.g. billing, personal, noreply.",
    )
    sequence = fields.Integer(default=10)

    # There is deliberately NO database-level unique constraint here, on any column.
    # base/wizard/base_partner_merge.py:167 asks _has_check_or_unique_constraint()
    # whether any CHECK or UNIQUE constraint touches the foreign key column it is
    # about to re-point -- partner_id. If one does, the UPDATE runs inside a
    # savepoint whose `except psycopg2.Error` handler falls back to
    # `DELETE FROM vmk_partner_email WHERE partner_id IN <every source id>` (:179).
    # A single colliding address during a contact merge would therefore destroy
    # every additional address of every source contact. Uniqueness lives in
    # _check_email_unique() below, which that raw SQL bypasses anyway.

    @api.depends("email")
    def _compute_email_normalized(self):
        for record in self:
            # strict=False matches mail.thread.blacklist._compute_email_normalized,
            # so a pasted "a@x.com, b@y.com" degrades the same way core's does.
            record.email_normalized = email_normalize(record.email, strict=False)

    @api.constrains("email", "partner_id")
    def _check_email_unique(self):
        """Reject an address the contact already holds, primary or additional.

        The same address may still appear on *several* contacts: core permits that
        and the mail helpers have a documented tie-break for it, so we add no
        restriction core does not have.
        """
        for record in self:
            normalized = record.email_normalized
            if not normalized:
                continue
            if normalized == record.partner_id.email_normalized:
                raise ValidationError(
                    self.env._(
                        "%(email)s is already the primary address of %(contact)s.",
                        email=record.email,
                        contact=record.partner_id.display_name,
                    )
                )
            duplicate = self.search(
                [
                    ("partner_id", "=", record.partner_id.id),
                    ("email_normalized", "=", normalized),
                    ("id", "!=", record.id),
                ],
                limit=1,
            )
            if duplicate:
                raise ValidationError(
                    self.env._(
                        "%(email)s is already an additional address of %(contact)s.",
                        email=record.email,
                        contact=record.partner_id.display_name,
                    )
                )

    # ------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------

    def action_promote_to_primary(self):
        """Swap this address with the contact's primary one.

        This is the one place the module writes to ``res.partner.email``, and it
        does not contradict the rule that it never does. The rule is that the
        module never writes there on its *own* initiative, behind the user's back;
        a button somebody presses is the user editing their own contact, with the
        bookkeeping done for them. ``email`` carries ``tracking=1``
        (mail/models/res_partner.py:21), so the swap lands in the chatter by itself.
        """
        self.ensure_one()
        partner = self.partner_id
        demoted = (partner.email or "").strip()
        demoted_normalized = email_normalize(demoted, strict=False)

        partner.email = self.email

        already_held = partner.vmk_email_ids.filtered(
            lambda row: row != self
            and demoted_normalized
            and row.email_normalized == demoted_normalized
        )
        if not demoted or already_held:
            # Nothing to demote, or the contact already keeps that address.
            self.unlink()
        else:
            # The label described the address that has just left, not the arriving one.
            self.write({"email": demoted, "label": False})
        return True

    # ------------------------------------------------------------
    # Matching
    # ------------------------------------------------------------

    @api.model
    def _resolve_partners(
        self,
        emails_normalized,
        ban_emails=None,
        filter_found=None,
        sort_key=None,
        sort_reverse=True,
    ):
        """Map normalized addresses to the contact holding them as an additional one.

        The single resolver behind all three matching overrides, so their behaviour
        cannot drift apart. Arguments mirror
        ``res.partner._find_or_create_from_emails`` and are applied the same way.

        :return: ``{normalized email: partner}``, omitting anything unmatched.
        :rtype: dict
        """
        wanted = {
            normalized
            for normalized in emails_normalized
            if normalized and normalized not in (ban_emails or [])
        }
        if not wanted:
            return {}

        # sudo() because deciding which contact owns an address is the same kind of
        # elevated bookkeeping as email_normalized's own compute_sudo=True, and
        # because callers include public/portal paths with no ACL on this model.
        # The partners themselves are handed back in the caller's environment.
        rows = self.sudo().search(
            [
                ("email_normalized", "in", list(wanted)),
                ("partner_id.active", "=", True),
            ],
            order="id ASC",
        )
        if not rows:
            return {}

        Partner = self.env["res.partner"]
        # A contact holding the address as its PRIMARY always wins, so installing
        # this module never re-routes mail that core already matched. Searched in
        # the caller's environment, exactly as core does.
        primary_holders = set(
            Partner.search([("email_normalized", "in", list(wanted))]).mapped(
                "email_normalized"
            )
        )

        candidate_ids = {}
        for row in rows:
            if row.email_normalized in primary_holders:
                continue
            candidate_ids.setdefault(row.email_normalized, set()).add(row.partner_id.id)

        resolved = {}
        for normalized, partner_ids in candidate_ids.items():
            # sorted() reproduces the 'id ASC' core searches with; sort_key then
            # re-orders exactly as _find_or_create_from_emails does.
            partners = Partner.browse(sorted(partner_ids))
            if filter_found:
                partners = partners.filtered(filter_found)
            if sort_key and len(partners) > 1:
                partners = partners.sorted(key=sort_key, reverse=sort_reverse)
            if partners:
                resolved[normalized] = partners[0]
        return resolved
