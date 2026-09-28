# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

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
    #
    # On 18, _update_foreign_keys_generic (base/wizard/base_partner_merge.py:103-159)
    # does not ask whether a constraint touches partner_id -- that check does not
    # exist yet. It instead counts this table's OTHER columns (:123-126): with only
    # one, it takes a per-record UPDATE guarded by NOT EXISTS; with more than one --
    # this table has nine (email, email_normalized, label, sequence, id, and the four
    # ORM housekeeping columns) -- it always takes the savepoint branch at :150-159,
    # a single bulk `UPDATE vmk_partner_email SET partner_id = %s WHERE partner_id IN
    # %s`, whose `except psycopg2.Error` falls back to
    # `DELETE FROM vmk_partner_email WHERE partner_id IN <every source id>` (:158).
    # That branch is chosen unconditionally for this table, regardless of whether a
    # constraint exists -- so, unlike 19, staying constraint-free does not route us
    # to a safer branch. What it does instead is remove anything for the UPDATE to
    # violate: with no unique or check constraint on partner_id, the bulk UPDATE
    # cannot raise psycopg2.Error for this table, so the DELETE fallback is never
    # reached and no address is ever deleted by a merge. See README.md and
    # ResPartner._vmk_dedupe_emails for what the bulk UPDATE does NOT do, which is
    # deduplicate: two source contacts sharing an address can still leave the
    # survivor holding it twice, since the plain UPDATE has no per-value comparison
    # to skip one. Uniqueness lives in _check_email_unique() below (which that raw
    # SQL bypasses) and in the post-merge dedupe pass, not in the database.

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
        (mail/models/res_partner.py:20), so the swap lands in the chatter by itself.
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
    def _resolve_partners(self, emails_normalized):
        """Map normalized addresses to the contact holding them as an additional one.

        The single resolver behind all four matching overrides (``res.partner``'s
        ``_find_or_create_from_emails`` and ``find_or_create``, and
        ``mail.thread``'s ``_mail_search_on_partner``), so their behaviour cannot
        drift apart.

        No ``ban_emails``, ``filter_found``, ``sort_key`` or ``sort_reverse`` here:
        those were core 19 additions to ``_find_or_create_from_emails`` that 18's
        version of the method does not have, so there is nothing for this resolver
        to mirror them onto. See ``res.partner._find_or_create_from_emails`` and
        README.md.

        :return: ``{normalized email: partner}``, omitting anything unmatched.
        :rtype: dict
        """
        wanted = {normalized for normalized in emails_normalized if normalized}
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
            # sorted() reproduces the 'id ASC' order core's own search uses.
            partners = Partner.browse(sorted(partner_ids))
            if partners:
                resolved[normalized] = partners[0]
        return resolved
