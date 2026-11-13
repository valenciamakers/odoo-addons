# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from urllib.parse import urlsplit, urlunsplit

from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError
from odoo.http import request

# Set by our controllers when the visitor holds a link that only the address
# received: a valid mailing token on core's subscription page, or our own
# confirmation link.
CONTEXT_PROVEN = "vmk_double_optin_proven"
# Set by the expiry cron, so a removal is logged as an expiry.
CONTEXT_EXPIRED = "vmk_double_optin_expired"


class VmkMailingConsentLog(models.Model):
    """One line per change to someone's consent to receive mailings.

    Written only by this module's own code, as superuser, and never changed
    afterwards: nobody has a create or write permission on it, and `write`
    refuses even the superuser. Settings administrators alone may delete a
    line, for an erasure request. Each line copies the email address and the
    list's name, so it still says what it recorded after the contact or the
    list is deleted.
    """

    _name = "vmk.mailing.consent.log"
    _description = "Consent Log"
    _order = "date desc, id desc"
    _rec_name = "email"

    date = fields.Datetime(
        string="Date", required=True, readonly=True, index=True, default=fields.Datetime.now
    )
    email = fields.Char(string="Email", required=True, readonly=True, index=True)
    contact_id = fields.Many2one(
        "mailing.contact",
        string="Mailing Contact",
        readonly=True,
        index="btree_not_null",
        ondelete="set null",
    )
    list_id = fields.Many2one(
        "mailing.list",
        string="Mailing List",
        readonly=True,
        index="btree_not_null",
        ondelete="set null",
    )
    list_name = fields.Char(string="Mailing List Name", readonly=True)
    action = fields.Selection(
        selection=[
            ("requested", "Confirmation Requested"),
            ("confirmed", "Confirmed"),
            ("subscribed", "Subscribed"),
            ("unsubscribed", "Unsubscribed"),
            ("reason", "Reason Given"),
            ("expired", "Expired"),
            ("removed", "Removed"),
            ("blacklisted", "Blacklisted"),
            ("unblacklisted", "Unblacklisted"),
        ],
        string="Action",
        required=True,
        readonly=True,
        index=True,
    )
    source = fields.Selection(
        selection=[
            ("website", "Website"),
            ("email_link", "Email Link"),
            ("backend", "Internal User"),
            ("import", "Imported"),
            ("system", "System"),
        ],
        string="Source",
        required=True,
        readonly=True,
    )
    user_id = fields.Many2one("res.users", string="User", readonly=True, ondelete="set null")
    ip_address = fields.Char(string="IP Address", readonly=True)
    user_agent = fields.Char(string="User Agent", readonly=True)
    url = fields.Char(string="Page", readonly=True)
    reason = fields.Char(string="Reason", readonly=True)

    def write(self, vals):
        raise UserError(_("Entries of the consent log cannot be changed."))

    # ------------------------------------------------------------
    # Writing the log
    # ------------------------------------------------------------

    @api.model
    def _vmk_source(self):
        """Where the change being made comes from, judged from the environment.

        `self.env.user` is the real user even under `sudo()`, which keeps the
        uid: core's website controllers subscribe visitors through a sudo
        environment of the public user. Scheduled actions and `odoo shell` run
        as the superuser, which is the system rather than anyone in the backend.
        """
        if self.env.context.get("import_file"):
            return "import"
        if self.env.context.get(CONTEXT_EXPIRED):
            return "system"
        if self.env.context.get(CONTEXT_PROVEN):
            return "email_link"
        if not self.env.user._is_internal():
            return "website"
        if self.env.user.id == api.SUPERUSER_ID:
            return "system"
        return "backend"

    @api.model
    def _vmk_request_values(self):
        """The visitor's IP address, user agent, and page, when there is a request.

        The page is the one the visitor was on (the referrer) for a JSON call,
        such as a newsletter form, and the requested page otherwise. Either way
        the query string is dropped: core's subscription pages carry the email
        address and a token there, and neither belongs in a permanent log.
        """
        if not request:
            return {}
        httprequest = request.httprequest
        page = httprequest.referrer if request.dispatcher.routing_type != "http" else None
        page = page or httprequest.base_url
        parts = urlsplit(page)
        return {
            "ip_address": httprequest.remote_addr,
            "user_agent": (httprequest.user_agent.string or "")[:512],
            "url": urlunsplit((parts.scheme, parts.netloc, parts.path, "", "")),
        }

    @api.model
    def _vmk_log(self, action, entries):
        """Write one line per entry, as superuser.

        :param str action: one of the `action` selection's keys;
        :param list entries: dicts with `email` and optionally `contact`,
          `mailing_list` (records) and `reason` (text). Entries without an
          email address are skipped: there is nothing to have consented with.
        """
        source = self._vmk_source()
        common = {
            "action": action,
            "source": source,
            "user_id": self.env.user.id,
            **self._vmk_request_values(),
        }
        vals_list = []
        for entry in entries:
            email = tools.email_normalize(entry.get("email") or "") or entry.get("email")
            if not email:
                continue
            mailing_list = entry.get("mailing_list")
            vals_list.append(
                {
                    **common,
                    "email": email,
                    "contact_id": entry.get("contact") and entry["contact"].id,
                    "list_id": mailing_list and mailing_list.id,
                    "list_name": mailing_list and mailing_list.name,
                    "reason": entry.get("reason"),
                }
            )
        return self.sudo().create(vals_list)

    @api.model
    def _vmk_log_subscriptions(self, action, subscriptions, reason=None):
        """Log `action` for each subscription, from its contact and list."""
        return self._vmk_log(
            action,
            [
                {
                    "email": sub.contact_id.email_normalized or sub.contact_id.email,
                    "contact": sub.contact_id,
                    "mailing_list": sub.list_id,
                    "reason": reason,
                }
                for sub in subscriptions.sudo()
            ],
        )
