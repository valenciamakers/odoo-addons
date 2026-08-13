# Copyright 2026 Valencia Makers, SL
# License MIT (https://opensource.org/licenses/MIT).

from odoo import api, models

from .sort_key import sort_app_blocks


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    @api.model
    def _get_view(self, view_id=None, view_type="form", **options):
        """Order the app blocks down the left of the Settings screen.

        The sidebar is drawn in arch order: `settings_form_compiler.js` walks
        `{selector: "app"}` in document order and `settings_page.js` sorts
        nothing. Each module adds its block with
        `<xpath expr="//form" position="inside">`, so the order you get is the
        order the inheriting views happened to be applied in. General Settings
        is only first because `base_setup` sets `priority` to 0.

        Sorting after `super()` is what makes this safe: the arch is fully
        combined by then, so every third-party xpath -- including
        `sale_management` flipping `sale`'s block to `notApp="0"` -- has already
        matched and cannot be broken by the reordering.

        The labels are already translated at this point, `arch_db` being a
        translated field, so each user gets the order that is alphabetical in
        their own language.
        """
        arch, view = super()._get_view(view_id, view_type, **options)
        if view_type == "form":
            sort_app_blocks(arch)
        return arch, view
