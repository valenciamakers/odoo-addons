// Copyright 2026 Valencia Makers, SL
// License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

import { registry } from "@web/core/registry";

// Opening the link shows a button; only clicking it confirms.
registry.category("web_tour.tours").add("vmk_mass_mailing_double_optin_confirm", {
    steps: () => [
        {
            content: "the page asks before confirming",
            trigger: `.o_vmk_confirm_subscription .alert-info:contains("Confirm your subscription to VMK Newsletter for tour@example.com.")`,
        },
        {
            content: "confirm",
            trigger: ".o_vmk_confirm_subscription button[type=submit]:contains('Confirm Subscription')",
            run: "click",
            expectUnloadPage: true,
        },
        {
            content: "the subscription is confirmed",
            trigger: `.o_vmk_confirm_subscription .alert-success:contains("You are now subscribed to VMK Newsletter from")`,
        },
    ],
});

// In the backend, a subscription awaiting confirmation says so, its link can
// be sent again, and the contact's Consent Log lists both requests.
registry.category("web_tour.tours").add("vmk_mass_mailing_double_optin_backend", {
    steps: () => [
        {
            content: "the subscription awaits confirmation",
            trigger: `.o_field_widget[name=subscription_ids] .o_data_row:contains("VMK Newsletter") .badge:contains("Awaiting Confirmation")`,
        },
        {
            content: "send the link again",
            trigger: `.o_field_widget[name=subscription_ids] .o_data_row:contains("VMK Newsletter") button[name=action_vmk_request_confirmation]:contains("Resend Confirmation")`,
            run: "click",
        },
        {
            content: "the form reloads with the second request counted",
            trigger: `.o_field_widget[name=subscription_ids] .o_data_row:contains("VMK Newsletter") .badge:contains("Awaiting Confirmation")`,
        },
        {
            // Core's form has five buttons already, so on a narrower screen
            // ours is the one the button box moves under More.
            // The form disables its buttons until the resend has finished.
            content: "open More, where the button box has one",
            trigger: ".o-form-buttonbox:not(:has(button[disabled]))",
            run() {
                document.querySelector(".o-form-buttonbox .o_button_more")?.click();
            },
        },
        {
            content: "open the contact's consent log",
            trigger: `button[name=action_vmk_view_consent_log]:contains("Consent Log"):contains("2")`,
            run: "click",
        },
        {
            content: "both requests are listed",
            trigger: `.o_list_view .o_data_row:contains("Confirmation Requested") ~ .o_data_row:contains("Confirmation Requested")`,
        },
    ],
});
