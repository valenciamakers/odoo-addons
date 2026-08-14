/** Copyright 2026 Valencia Makers, SL
 *  License MIT (https://opensource.org/licenses/MIT). */

import { registry } from "@web/core/registry";
import { EmailField, emailField } from "@web/views/fields/email/email_field";

/**
 * The email field, with the envelope that the contact form has.
 *
 * Odoo registers two variants: `email` and `form.email`, and the registry
 * resolves `widget="email"` to `form.email` in a form view but to the plain
 * `email` in a list. Only the form variant draws the envelope, and only in its
 * edit branch -- which never renders for a row nobody is editing. So a list can
 * not get that affordance by naming an existing widget.
 *
 * This adds the same `mailto:` anchor to both branches. It is a link handed to
 * the browser, exactly as the contact form's is: nothing is sent through Odoo,
 * so the module's rule that additional addresses are never mailed by us still
 * holds.
 */
export class VmkEmailLinkField extends EmailField {
    static template = "vmk_partner_email_multiple.EmailLinkField";
}

export const vmkEmailLinkField = {
    ...emailField,
    component: VmkEmailLinkField,
};

registry.category("fields").add("vmk_email_link", vmkEmailLinkField);
