# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import http
from odoo.http import request

from odoo.addons.mass_mailing.controllers import main

from ..models.vmk_mailing_consent_log import CONTEXT_PROVEN


class MassMailController(main.MassMailController):
    @http.route()
    def mailing_update_list_subscription(
        self,
        mailing_id=None,
        document_id=None,
        email=None,
        hash_token=None,
        lists_optin_ids=None,
        **post,
    ):
        """Core's subscription page, reached from a link in a mailing.

        With a `hash_token`, core refuses the request unless the token was
        made for that address by that mailing, and only someone reading the
        address has it. So a list chosen there needs no further confirmation.
        Without one, the visitor is a signed-in user managing their own
        account's address, which nothing has proven, and the usual rule holds.
        """
        if hash_token:
            request.update_context(**{CONTEXT_PROVEN: True})
        return super().mailing_update_list_subscription(
            mailing_id=mailing_id,
            document_id=document_id,
            email=email,
            hash_token=hash_token,
            lists_optin_ids=lists_optin_ids,
            **post,
        )


class MailingDoubleOptInController(http.Controller):
    @http.route(
        "/mailing/subscription/<int:subscription_id>/confirm",
        type="http",
        auth="public",
        website=True,
        sitemap=False,
        methods=["GET", "POST"],
    )
    def vmk_confirm_subscription(self, subscription_id, token=None, **post):
        """Show a confirmation button on GET, and confirm only on its POST.

        Mail security gateways open the links in an email to scan them, so a
        link that confirmed on GET would confirm subscriptions nobody asked
        for. Core's unsubscription page asks for a click the same way. A wrong
        token and a subscription that does not exist get the same page, so
        the route reveals nothing about which subscriptions exist.
        """
        subscription = request.env["mailing.subscription"].sudo().browse(subscription_id).exists()
        if not subscription or not subscription._vmk_check_confirmation_token(token):
            return self._vmk_render_invalid()

        values = {
            "list_name": subscription.list_id.name,
            "company_name": request.env.company.name,
        }
        if subscription.vmk_confirmation_state == "confirmed" and not subscription.opt_out:
            return self._vmk_render_confirmed(values)
        if (
            subscription.vmk_confirmation_state != "pending"
            or subscription.opt_out
            or subscription._vmk_confirmation_expired()
        ):
            return self._vmk_render_invalid()

        if request.httprequest.method == "POST":
            # The visitor holds a link only the address received.
            request.update_context(**{CONTEXT_PROVEN: True})
            request.env["mailing.subscription"].sudo().browse(subscription.id)._vmk_confirm()
            return self._vmk_render_confirmed(values)

        return request.render(
            "vmk_mass_mailing_double_optin.page_confirm_subscription",
            {
                "message": request.env._(
                    "Confirm your subscription to %(list)s for %(email)s.",
                    list=values["list_name"],
                    email=subscription.contact_id.email,
                ),
                "action_url": f"/mailing/subscription/{subscription.id}/confirm",
                "token": token,
            },
        )

    def _vmk_render_confirmed(self, values):
        return request.render(
            "vmk_mass_mailing_double_optin.page_subscription_confirmed",
            {
                "message": request.env._(
                    "You are now subscribed to %(list)s from %(company)s.",
                    list=values["list_name"],
                    company=values["company_name"],
                ),
            },
        )

    def _vmk_render_invalid(self):
        return request.render("vmk_mass_mailing_double_optin.page_subscription_link_invalid")
