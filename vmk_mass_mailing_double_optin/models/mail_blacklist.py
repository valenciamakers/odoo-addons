# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import api, models, tools


class MailBlacklist(models.Model):
    """Log blacklisting, which stops every mailing to an address at once.

    Core blacklists from the unsubscription page ("Blacklist me" on every
    list), and unblacklists by archiving the entry rather than deleting it.
    """

    _inherit = "mail.blacklist"

    @api.model_create_multi
    def create(self, vals_list):
        # Core's `create` returns the existing entry for an address it already
        # has, so tell those apart from the ones it actually creates.
        emails = [tools.email_normalize(vals.get("email") or "") for vals in vals_list]
        existing = set(
            self.sudo()
            .with_context(active_test=False)
            .search([("email", "in", [email for email in emails if email])])
            .ids
        )
        records = super().create(vals_list)
        self.env["vmk.mailing.consent.log"]._vmk_log(
            "blacklisted",
            [{"email": rec.email} for rec in records if rec.id not in existing and rec.active],
        )
        return records

    def write(self, vals):
        if "active" not in vals:
            return super().write(vals)
        before = {rec.id: rec.active for rec in self}
        result = super().write(vals)
        changed = self.filtered(lambda rec: rec.active != before[rec.id])
        Log = self.env["vmk.mailing.consent.log"]
        Log._vmk_log("blacklisted", [{"email": rec.email} for rec in changed if rec.active])
        Log._vmk_log("unblacklisted", [{"email": rec.email} for rec in changed if not rec.active])
        return result

    def unlink(self):
        self.env["vmk.mailing.consent.log"]._vmk_log(
            "unblacklisted", [{"email": rec.email} for rec in self if rec.active]
        )
        return super().unlink()
