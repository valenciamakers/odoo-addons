# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import _, api, fields, models, tools

from .mailing_subscription import SEEN_REMOVED


class MailingContact(models.Model):
    _inherit = "mailing.contact"

    vmk_consent_log_count = fields.Integer(
        string="Consent Log Count", compute="_compute_vmk_consent_log_count"
    )

    def _compute_vmk_consent_log_count(self):
        Log = self.env["vmk.mailing.consent.log"]
        if not Log.has_access("read"):
            self.vmk_consent_log_count = 0
            return
        counts = dict(
            Log._read_group(
                [("email", "in", [c.email_normalized for c in self if c.email_normalized])],
                ["email"],
                ["__count"],
            )
        )
        for contact in self:
            contact.vmk_consent_log_count = counts.get(contact.email_normalized, 0)

    @api.model_create_multi
    def create(self, vals_list):
        contacts = super().create(vals_list)
        contacts._vmk_process_new_subscriptions(set())
        return contacts

    def write(self, vals):
        """Log what a write to `list_ids` adds and removes.

        `list_ids` is a many2many over `mailing.subscription`'s own table, so
        the ORM inserts and deletes those rows directly, without calling the
        subscription's `create` or `unlink`.
        """
        if "list_ids" not in vals:
            return super().write(vals)
        before = {
            sub.id: (sub.contact_id, sub.list_id, sub.contact_id.email_normalized)
            for sub in self.sudo().subscription_ids
        }
        result = super().write(vals)
        self.invalidate_recordset(["list_ids", "subscription_ids"])
        current = set(self.sudo().subscription_ids.ids)
        removed = self.env.cr.cache.setdefault(SEEN_REMOVED, set())
        gone = [sub_id for sub_id in before if sub_id not in current and sub_id not in removed]
        removed.update(gone)
        self.env["vmk.mailing.consent.log"]._vmk_log(
            "removed",
            [
                {"email": before[sub_id][2], "contact": before[sub_id][0].exists(),
                 "mailing_list": before[sub_id][1].exists()}
                for sub_id in gone
            ],
        )
        self._vmk_process_new_subscriptions(set(before))
        return result

    def unlink(self):
        """Log the subscriptions the database deletes with the contacts."""
        removed = self.env.cr.cache.setdefault(SEEN_REMOVED, set())
        subscriptions = self.sudo().subscription_ids.filtered(lambda sub: sub.id not in removed)
        removed.update(subscriptions.ids)
        self.env["vmk.mailing.consent.log"]._vmk_log_subscriptions("removed", subscriptions)
        return super().unlink()

    def _vmk_process_new_subscriptions(self, known_ids):
        """Treat subscriptions the ORM inserted through `list_ids` as created."""
        self.invalidate_recordset(["subscription_ids"])
        new = self.sudo().subscription_ids.filtered(lambda sub: sub.id not in known_ids)
        # `_vmk_on_create` skips those `mailing.subscription.create` already saw.
        # The environment stays the caller's, whose user decides about confirmation.
        new.with_env(self.env)._vmk_on_create()

    def action_vmk_view_consent_log(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "vmk_mass_mailing_double_optin.vmk_mailing_consent_log_action"
        )
        action["domain"] = [("email", "=", tools.email_normalize(self.email) or self.email)]
        action["context"] = {}
        action["name"] = _("Consent Log")
        return action
