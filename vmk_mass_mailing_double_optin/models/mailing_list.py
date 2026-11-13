# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import fields, models

from .mailing_subscription import SEEN_REMOVED


class MailingList(models.Model):
    _inherit = "mailing.list"

    vmk_double_optin = fields.Boolean(
        string="Double Opt-In",
        default=True,
        help="People who subscribe on the website receive an email, and only receive mailings "
        "from this list once they confirm through it.",
    )

    def _mailing_get_opt_out_list(self, mailing):
        """Add the addresses still awaiting confirmation to core's opt-outs.

        Core keeps an address that is opted out of one of the mailing's lists
        but subscribed to another, so an address awaiting confirmation on one
        list still receives the mailing through a list it is subscribed to.
        Core's own set already counts an awaited subscription as subscribed;
        the union below corrects that, rather than replacing core's set.
        """
        opt_out = super()._mailing_get_opt_out_list(mailing)
        subscriptions = self.subscription_ids if self else mailing.contact_list_ids.subscription_ids
        pending = subscriptions.filtered(
            lambda sub: not sub.opt_out and sub.vmk_confirmation_state == "pending"
        )
        if not pending:
            return opt_out
        receiving = set(
            (subscriptions - pending)
            .filtered(lambda sub: not sub.opt_out)
            .mapped("contact_id.email_normalized")
        )
        awaiting = {
            email
            for email in pending.mapped("contact_id.email_normalized")
            if email and email not in receiving
        }
        return set(opt_out) | awaiting

    def unlink(self):
        """Log the subscriptions the database deletes with the lists."""
        removed = self.env.cr.cache.setdefault(SEEN_REMOVED, set())
        subscriptions = self.sudo().subscription_ids.filtered(lambda sub: sub.id not in removed)
        removed.update(subscriptions.ids)
        self.env["vmk.mailing.consent.log"]._vmk_log_subscriptions("removed", subscriptions)
        return super().unlink()
