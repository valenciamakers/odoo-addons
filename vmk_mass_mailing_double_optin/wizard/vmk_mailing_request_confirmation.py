# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.base.models.res_partner import _lang_get


class VmkMailingRequestConfirmation(models.TransientModel):
    """Email a confirmation link to many mailing contacts at once.

    For contacts added without one, by a user or an import: each subscription
    to the chosen lists that has never been asked to confirm is marked as
    awaiting confirmation and sent the link, exactly as the contact form's
    Request Confirmation button does for one.
    """

    _name = "vmk.mailing.request.confirmation"
    _description = "Request Confirmation"

    contact_ids = fields.Many2many("mailing.contact", string="Mailing Contacts")
    # Named as core's own field on mailing.contact, so the `default_list_ids`
    # a mailing list's Recipients button puts in the context fills it in.
    list_ids = fields.Many2many("mailing.list", string="Mailing Lists", required=True)
    lang = fields.Selection(
        _lang_get,
        string="Language",
        required=True,
        default=lambda self: self.env.lang or self.env.user.lang,
        help="Used for contacts whose language is unknown or unspecified.",
    )
    subscription_ids = fields.Many2many(
        "mailing.subscription", compute="_compute_subscription_ids", string="Subscriptions"
    )
    subscription_count = fields.Integer(compute="_compute_subscription_ids")
    summary = fields.Text(compute="_compute_summary")

    @api.depends("contact_ids", "list_ids")
    def _compute_subscription_ids(self):
        for wizard in self:
            lists = wizard.list_ids._origin
            subscriptions = wizard.contact_ids._origin.subscription_ids.filtered(
                lambda sub, lists=lists: sub.list_id in lists
                and not sub.opt_out
                and not sub.vmk_confirmation_state
                and sub.contact_id.email_normalized
                and not sub.contact_id.is_blacklisted
            )
            wizard.subscription_ids = subscriptions
            wizard.subscription_count = len(subscriptions)

    @api.depends("subscription_count")
    def _compute_summary(self):
        skipped = _(
            "Contacts already confirmed, or awaiting confirmation, unsubscribed, blacklisted, or "
            "without an email address are skipped."
        )
        for wizard in self:
            count = wizard.subscription_count
            if not count:
                text = _(
                    "None of these contacts has a subscription to these lists that can be asked "
                    "for confirmation."
                )
            elif count == 1:
                text = _(
                    "1 confirmation email will be sent. Until the contact confirms their "
                    "subscription, they will not receive mailings from the list."
                )
            else:
                text = _(
                    "%(count)s confirmation emails will be sent. Until each contact confirms "
                    "their subscription, they will not receive mailings from the list.",
                    count=count,
                )
            wizard.summary = f"{text}\n\n{skipped}"

    def action_request_confirmation(self):
        self.ensure_one()
        subscriptions = self.subscription_ids
        if not subscriptions:
            raise UserError(
                _(
                    "None of these contacts has a subscription to these lists that can be asked "
                    "for confirmation."
                )
            )
        # Everything after this runs as superuser.
        subscriptions.check_access("write")
        subscriptions._vmk_request_confirmation(resend=True, lang=self.lang)
        count = len(subscriptions)
        message = (
            _("1 confirmation request sent.")
            if count == 1
            else _("%(count)s confirmation requests sent.", count=count)
        )
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "message": message,
                "type": "success",
                "sticky": False,
                "next": {"type": "ir.actions.act_window_close"},
            },
        }
