/** Copyright 2026 Valencia Makers, SL
 *  License MIT (https://opensource.org/licenses/MIT). */

import { Component, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownGroup } from "@web/core/dropdown/dropdown_group";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { user } from "@web/core/user";
import { localization } from "@web/core/l10n/localization";
import { browser } from "@web/core/browser/browser";
import { session } from "@web/session";

/** Key of the `ir.config_parameter` that opts the language name into the button. */
const SHOW_NAME_PARAM = "vmk_language_systray.show_name";

/**
 * A systray dropdown that sets the *current user's* backend language and
 * reloads. Deliberately backend-only: it writes `res.users.lang`, never
 * `website`'s frontend language.
 */
export class LanguageSystray extends Component {
    static template = "vmk_language_systray.LanguageSystray";
    static components = { Dropdown, DropdownGroup, DropdownItem };
    static props = {};

    setup() {
        this.orm = useService("orm");
        this.languages = [];

        onWillStart(async () => {
            // res.lang.get_installed() is @api.model and base.group_user has
            // read access on res.lang (base/security/ir.model.access.csv),
            // so a plain internal user can call this directly -- no sudo, no
            // server-side wrapper.
            //
            // Its order already reflects vmk_language_sequence's ordering
            // when that module is installed: get_installed() reads
            // _get_active_by(), which that module overrides to sort by
            // (sequence, name) instead of core's plain (name). Sorting the
            // result again here would undo that, so it is used exactly as
            // returned.
            const installed = await this.orm.call("res.lang", "get_installed", []);
            this.languages = installed.map(([code, name]) => ({
                code,
                // Core displays language names the same way, e.g.
                // portal.language_selector: name.split('/').pop(). That
                // leaves a leading space on names like "Spanish / Español"
                // -- core gets away with it because it only ever lands in
                // HTML text, where the space collapses. We also put it in
                // `title`/`aria-label`, where it would not, hence the trim.
                name: name.split("/").pop().trim(),
            }));
        });
    }

    // localization.code is the current user's language in Odoo form
    // (e.g. "es_ES"), set by the localization service once it starts.
    // user.lang is the *browser* locale form ("es-ES") and never equals a
    // res.lang code, so it cannot be used for this comparison.
    isActive(lang) {
        return lang.code === localization.code;
    }

    get activeLanguage() {
        return this.languages.find((lang) => this.isActive(lang));
    }

    /**
     * Whether to print the current language beside the globe.
     *
     * Off by default: the systray is a crowded, fixed-width row, and a word
     * as wide as "English (US)" earns its space only for someone who has
     * asked for it. `models/ir_http.py` puts the flag in `session_info`, so
     * this costs no request of its own.
     */
    get showName() {
        return Boolean(session[SHOW_NAME_PARAM]);
    }

    /**
     * The button's accessible name, and its tooltip.
     *
     * It has to say what the control *does*, not merely what it currently
     * reads: below the `lg` breakpoint the name span is hidden and the
     * button is a bare globe, so "Español" alone would be announced as
     * "Español, button" with nothing to suggest it changes anything. Core
     * makes the same distinction for the equivalent control -- see
     * `switch_company_item.xml`, whose aria-label is `'Switch to ' +
     * props.company.name` rather than the company name on its own.
     *
     * Naming the language inside the label rather than replacing it keeps
     * the accessible name a superset of the visible text at `lg` and up,
     * which is what WCAG 2.5.3 (Label in Name) asks for.
     *
     * The fallback matters more than it looks. `activeLanguage` is undefined
     * whenever `localization.code` is not among the installed languages --
     * the localization service falls back to `browser.navigator.language`
     * when the user's context carries no lang, so a browser set to, say,
     * en-GB against a database without it lands here. Without the fallback
     * the button would have no accessible name at all.
     */
    get buttonLabel() {
        const active = this.activeLanguage;
        return active ? _t("Language: %s", active.name) : _t("Language");
    }

    async selectLanguage(code) {
        if (code === localization.code) {
            return;
        }
        // `lang` must be the only key in this write. res.users.write() only
        // takes the sudo-free self-write path (base/models/res_users.py)
        // when *every* key in vals is in SELF_WRITEABLE_FIELDS -- one
        // unlisted key anywhere in the call and the whole write falls back
        // to needing write access on res.users, which a plain internal user
        // does not have.
        await this.orm.write("res.users", [user.userId], { lang: code });
        browser.location.reload();
    }
}

export const systrayItem = {
    Component: LanguageSystray,
    // Gate mounting on this, rather than a t-if in the template, so the
    // component -- and its onWillStart RPC -- never runs at all in a
    // single-language database. `multiLang` is set by the localization
    // service to len(res.lang.get_installed()) > 1.
    isDisplayed: () => localization.multiLang,
};

// The navbar's systrayItems getter (web/static/src/webclient/navbar/navbar.js)
// reverses this list before rendering, so a *lower* sequence ends up
// *further right*. web.user_menu is 0 and SwitchCompanyMenu is 1; 2 sits
// immediately to their left.
registry.category("systray").add("vmk_language_systray.LanguageSystray", systrayItem, {
    sequence: 2,
});
