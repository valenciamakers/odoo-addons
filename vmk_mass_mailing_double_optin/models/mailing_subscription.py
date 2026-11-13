# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from datetime import timedelta
from urllib.parse import urlencode, urljoin

from odoo import api, fields, models, tools
from odoo.http import request

from .vmk_mailing_consent_log import CONTEXT_EXPIRED, CONTEXT_PROVEN

# How long a confirmation link works. The email says so in words, so a change
# here is a change to the template's wording and its translations too.
CONFIRMATION_VALIDITY = timedelta(days=7)
# A new request within this time sends no second email; the first link stays valid.
RESEND_INTERVAL = timedelta(minutes=10)
TOKEN_SCOPE = "vmk_mass_mailing_double_optin-confirm"
TEMPLATE_XMLID = "vmk_mass_mailing_double_optin.mail_template_confirmation"
# Keys of `cr.cache`, which lives as long as the transaction: subscriptions
# this module has already logged as created, or as removed.
SEEN_CREATED = "vmk_double_optin_created"
SEEN_REMOVED = "vmk_double_optin_removed"


class MailingSubscription(models.Model):
    _inherit = "mailing.subscription"

    vmk_confirmation_state = fields.Selection(
        selection=[("pending", "Awaiting Confirmation"), ("confirmed", "Confirmed")],
        string="Confirmation",
        readonly=True,
        copy=False,
        index="btree_not_null",
        help="Empty when no confirmation was asked for: the subscription was added by a user, "
        "or the mailing list does not require double opt-in.",
    )
    vmk_confirmation_requested = fields.Datetime(
        string="Confirmation Requested", readonly=True, copy=False
    )
    vmk_confirmation_date = fields.Datetime(string="Confirmation Date", readonly=True, copy=False)
    vmk_confirmation_lang = fields.Char(string="Confirmation Language", readonly=True, copy=False)

    # ------------------------------------------------------------
    # ORM
    # ------------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        subscriptions = super().create(vals_list)
        subscriptions._vmk_on_create()
        return subscriptions

    def write(self, vals):
        if not {"opt_out", "opt_out_reason_id", "opt_out_datetime"} & vals.keys():
            return super().write(vals)
        before = {sub.id: (sub.opt_out, sub.opt_out_reason_id) for sub in self.sudo()}
        result = super().write(vals)
        Log = self.env["vmk.mailing.consent.log"]

        unsubscribed = self.filtered(lambda sub: sub.opt_out and not before[sub.id][0])
        for reason, subs in unsubscribed.grouped("opt_out_reason_id").items():
            Log._vmk_log_subscriptions("unsubscribed", subs, reason=reason.name or None)
        if unsubscribed.filtered("vmk_confirmation_state"):
            # Whatever was confirmed or awaited ends with the subscription.
            unsubscribed.sudo().write({"vmk_confirmation_state": False})

        # Core asks for the reason on a second page, after the unsubscription.
        reason_given = (self - unsubscribed).filtered(
            lambda sub: sub.opt_out
            and sub.opt_out_reason_id
            and sub.opt_out_reason_id != before[sub.id][1]
        )
        for reason, subs in reason_given.grouped("opt_out_reason_id").items():
            Log._vmk_log_subscriptions("reason", subs, reason=reason.name)

        self.filtered(lambda sub: not sub.opt_out and before[sub.id][0])._vmk_subscribe()
        return result

    def unlink(self):
        removed = self.env.cr.cache.setdefault(SEEN_REMOVED, set())
        to_log = self.filtered(lambda sub: sub.id not in removed)
        removed.update(to_log.ids)
        action = "expired" if self.env.context.get(CONTEXT_EXPIRED) else "removed"
        self.env["vmk.mailing.consent.log"]._vmk_log_subscriptions(action, to_log)
        return super().unlink()

    # ------------------------------------------------------------
    # Subscribing and confirming
    # ------------------------------------------------------------

    def _vmk_on_create(self):
        """Log new subscriptions, and ask for confirmation where it is needed.

        Called from `create`, and by `mailing.contact` for the subscriptions its
        `list_ids` creates: that field is a many2many over this model's table,
        so the ORM inserts those rows without calling `create`.
        """
        created = self.env.cr.cache.setdefault(SEEN_CREATED, set())
        subscriptions = self.filtered(lambda sub: sub.id not in created)
        created.update(subscriptions.ids)
        opted_out = subscriptions.filtered("opt_out")
        self.env["vmk.mailing.consent.log"]._vmk_log_subscriptions("unsubscribed", opted_out)
        (subscriptions - opted_out)._vmk_subscribe()

    def _vmk_subscribe(self):
        """Subscriptions that just began, or began again after an unsubscription."""
        to_confirm = self._vmk_needing_confirmation()
        self.env["vmk.mailing.consent.log"]._vmk_log_subscriptions("subscribed", self - to_confirm)
        to_confirm._vmk_request_confirmation()

    def _vmk_needing_confirmation(self):
        """The subscriptions of `self` that have to wait for a confirmation.

        A subscription made by anyone who is not an internal user, on a list
        requiring double opt-in, for a contact with an email address. Users
        adding contacts in the backend vouch for them, and core's subscription
        page, reached through a link from a mailing, has already proven the
        visitor reads that address (`CONTEXT_PROVEN`).
        """
        if (
            self.env.context.get(CONTEXT_PROVEN)
            or self.env.context.get("import_file")
            or self.env.user._is_internal()
        ):
            return self.browse()
        return self.sudo().filtered(
            lambda sub: sub.list_id.vmk_double_optin and sub.contact_id.email_normalized
        )

    def _vmk_request_confirmation(self, resend=False):
        """Mark as awaiting confirmation, and email each a confirmation link.

        A subscription asked less than `RESEND_INTERVAL` ago gets no second
        email, unless `resend`: its first link still works, and a form
        submitted repeatedly cannot flood an inbox.
        """
        subscriptions = self.sudo()
        if not subscriptions:
            return
        now = fields.Datetime.now()
        recent = subscriptions.browse()
        if not resend:
            recent = subscriptions.filtered(
                lambda sub: sub.vmk_confirmation_requested
                and sub.vmk_confirmation_requested > now - RESEND_INTERVAL
            )
        recent.write({"vmk_confirmation_state": "pending"})

        to_send = subscriptions - recent
        visitor = not self.env.user._is_internal()
        for sub in to_send:
            sub.write(
                {
                    "vmk_confirmation_state": "pending",
                    "vmk_confirmation_requested": now,
                    "vmk_confirmation_lang": (visitor and self.env.lang)
                    or sub.vmk_confirmation_lang
                    or sub.contact_id.partner_id.lang
                    or self.env.lang,
                }
            )
        if to_send:
            # The website the visitor signed up on, by its configured domain:
            # never the request's Host header, which the visitor controls.
            website = request and visitor and getattr(request, "website", None)
            base_url = website.get_base_url() if website else None
            urls = {sub.id: sub._vmk_confirmation_url(base_url) for sub in to_send}
            template = self.env.ref(TEMPLATE_XMLID).sudo()
            template.with_context(vmk_confirmation_urls=urls).send_mail_batch(to_send.ids)
            self.env.ref("mail.ir_cron_mail_scheduler_action").sudo()._trigger()
        self.env["vmk.mailing.consent.log"]._vmk_log_subscriptions("requested", subscriptions)

    def _vmk_confirmation_token(self):
        """A signature of the subscription, its address, and when it was asked.

        Nothing is stored: the token is computed again to check it. A new
        request changes the time and so invalidates the previous link, and so
        does a change of the contact's address.
        """
        self.ensure_one()
        message = (
            self.id,
            self.contact_id.email_normalized or "",
            fields.Datetime.to_string(self.vmk_confirmation_requested),
        )
        return tools.hmac(self.env(su=True), TOKEN_SCOPE, message)

    def _vmk_check_confirmation_token(self, token):
        self.ensure_one()
        return bool(
            token
            and isinstance(token, str)
            and self.vmk_confirmation_requested
            and tools.consteq(token, self._vmk_confirmation_token())
        )

    def _vmk_confirmation_expired(self):
        self.ensure_one()
        return self.vmk_confirmation_requested + CONFIRMATION_VALIDITY < fields.Datetime.now()

    def _vmk_confirmation_url(self, base_url=None):
        self.ensure_one()
        path = f"/mailing/subscription/{self.id}/confirm?" + urlencode(
            {"token": self._vmk_confirmation_token()}
        )
        return urljoin(base_url or self.get_base_url(), path)

    def _vmk_confirm(self):
        """Confirm the subscriptions awaiting it; the controller has checked the token."""
        pending = self.sudo().filtered(
            lambda sub: sub.vmk_confirmation_state == "pending" and not sub.opt_out
        )
        pending.write(
            {"vmk_confirmation_state": "confirmed", "vmk_confirmation_date": fields.Datetime.now()}
        )
        self.env["vmk.mailing.consent.log"]._vmk_log_subscriptions("confirmed", pending)
        return pending

    # ------------------------------------------------------------
    # Actions and cron
    # ------------------------------------------------------------

    def action_vmk_request_confirmation(self):
        """Email a confirmation link: again, or to someone subscribed without one.

        Callable by any user over RPC, so it checks the caller may write these
        subscriptions before it does anything as superuser.
        """
        self.check_access("write")
        self.filtered(
            lambda sub: not sub.opt_out
            and sub.vmk_confirmation_state != "confirmed"
            and sub.contact_id.email_normalized
        )._vmk_request_confirmation(resend=True)
        return True

    @api.model
    def _cron_vmk_expire_confirmations(self):
        """Remove subscriptions nobody confirmed before their link expired.

        A contact the website created for that signup alone is removed with
        it, since nothing else of ours needs it. The consent log keeps a line
        for each, as proof of what was asked and when.
        """
        limit = fields.Datetime.now() - CONFIRMATION_VALIDITY
        expired = self.sudo().search(
            [
                ("vmk_confirmation_state", "=", "pending"),
                ("vmk_confirmation_requested", "<", limit),
            ]
        )
        if not expired:
            return
        contacts = expired.contact_id
        expired.with_context(**{CONTEXT_EXPIRED: True}).unlink()
        orphans = contacts.exists().filtered(
            lambda contact: not contact.subscription_ids
            and not (contact.create_uid and contact.create_uid._is_internal())
        )
        orphans.with_context(**{CONTEXT_EXPIRED: True}).unlink()
