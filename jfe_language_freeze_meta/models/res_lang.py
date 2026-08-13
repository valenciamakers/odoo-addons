# Copyright 2026 Valencia Makers, SL
# License MIT (https://opensource.org/licenses/MIT).

from odoo import api, fields, models

# Fields Odoo re-applies to `res.lang` from its own data files: every column of
# `base/data/res.lang.csv`, plus the two `res_lang_data.xml` sets outside its
# `noupdate` block. Editing any of them by hand is what this module protects.
# `active` and `sequence` are deliberately absent -- enabling a language, or
# dragging it into order, is not a customisation worth freezing the record for.
PROTECTED_FIELDS = frozenset(
    {
        "name",
        "code",
        "iso_code",
        "url_code",
        "direction",
        "grouping",
        "decimal_point",
        "thousands_sep",
        "date_format",
        "time_format",
        "week_start",
        "flag_image",
    }
)


class ResLang(models.Model):
    _inherit = "res.lang"

    protect_from_updates = fields.Boolean(
        string="Protect From Updates",
        compute="_compute_protect_from_updates",
        inverse="_inverse_protect_from_updates",
        help="Keep this language's settings when Odoo modules are updated.\n\n"
        "Odoo ships language records as module data and re-applies them on every "
        "update, reverting edits to the name, ISO code, formats and so on. This "
        "is set automatically when you edit one of those fields; untick it to let "
        "Odoo manage this language again.",
    )

    def _compute_protect_from_updates(self):
        protected = {
            data["res_id"]: data["noupdate"]
            for data in self.env["ir.model.data"]
            .sudo()
            .search_read(
                [("model", "=", "res.lang"), ("res_id", "in", self.ids)],
                ["res_id", "noupdate"],
            )
        }
        for lang in self:
            # A language with no external id -- one added by hand -- is in no data
            # file, so nothing will ever overwrite it and there is nothing to set.
            lang.protect_from_updates = protected.get(lang.id, False)

    def _inverse_protect_from_updates(self):
        for lang in self:
            lang._set_update_protection(lang.protect_from_updates)

    def _set_update_protection(self, protect):
        """Flip `noupdate` on these languages' external ids.

        `_load_records` skips a record whose external id carries ``noupdate``
        while updating a module, and the xmlid upsert never writes that column
        back, so the flag survives every later update.
        """
        self.env["ir.model.data"].sudo().search(
            [("model", "=", "res.lang"), ("res_id", "in", self.ids)]
        ).noupdate = protect
        self.invalidate_recordset(["protect_from_updates"])

    def _load_records_write(self, values):
        # The module data loader reaches writes through here; a person editing the
        # form does not. Without the marker, the first update after install would
        # look like a customisation and freeze every language it touched.
        return super(
            ResLang, self.with_context(jfe_loading_module_data=True)
        )._load_records_write(values)

    def write(self, vals):
        res = super().write(vals)
        if not self.env.context.get("jfe_loading_module_data") and (
            PROTECTED_FIELDS & vals.keys()
        ):
            self._set_update_protection(True)
        return res
