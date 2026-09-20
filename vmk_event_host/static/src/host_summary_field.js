/** @odoo-module **/
// Copyright 2026 Valencia Makers, SL
// License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

import { Component, useRef } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

/**
 * Read-only summary of an event's hosts that sends you to the tab holding
 * them, the way clicking a field usually puts you where you can edit it.
 *
 * The notebook keeps its active page in component state with no public way in,
 * so this clicks the tab the user would have clicked. The tab carries a `name`
 * in the DOM (`Notebook`'s template renders `t-att-name` on each `.nav-link`),
 * which is what makes that findable without depending on tab order or label.
 */
export class VmkHostSummaryField extends Component {
    static template = "vmk_event_host.HostSummaryField";
    static props = {
        ...standardFieldProps,
        page: { type: String },
        placeholder: { type: String, optional: true },
    };

    setup() {
        this.root = useRef("root");
    }

    get value() {
        return this.props.record.data[this.props.name] || "";
    }

    get label() {
        return this.value
            ? _t("%s — show the Hosts tab", this.value)
            : _t("Show the Hosts tab");
    }

    showPage() {
        const tab = this.root.el
            ?.closest(".o_form_renderer")
            ?.querySelector(`.o_notebook .nav-link[name="${this.props.page}"]`);
        tab?.click();
        tab?.scrollIntoView({ block: "nearest" });
    }
}

registry.category("fields").add("vmk_host_summary", {
    component: VmkHostSummaryField,
    displayName: _t("Host summary"),
    supportedTypes: ["char"],
    supportedOptions: [
        {
            label: _t("Notebook page"),
            name: "page",
            type: "string",
            help: _t("Name of the notebook page this summary opens."),
        },
    ],
    extractProps: ({ options, placeholder }) => ({
        page: options.page,
        placeholder,
    }),
});
