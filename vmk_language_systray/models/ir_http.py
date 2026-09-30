# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import models

SHOW_NAME_PARAM = "vmk_language_systray.show_name"


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    def session_info(self):
        """Expose the opt-in "show the language name" flag to the web client.

        The flag is an ``ir.config_parameter`` rather than a field on a model
        of ours, because that is the one hidden switch in Odoo that already
        has somewhere to set it by hand: Settings > Technical > System
        Parameters. Nothing in this module puts it on a settings page, and
        nothing needs to.

        It travels in ``session_info`` rather than being fetched by the
        component because ``ir.config_parameter`` is readable only by
        ``base.group_system`` (``base/security/ir.model.access.csv``), so a
        plain internal user cannot query it directly -- the ``sudo()`` here is
        what makes it visible to everyone at all. Core solves the identical
        problem the identical way one screen up, in ``web/models/ir_http.py``:
        ``"quick_login": IrConfigSudo.get_bool('web.quick_login', True)``.

        ``get_bool`` because a system parameter is free-text -- someone typing
        ``true`` or ``1`` in that screen means the same thing as ``True``, and
        anything unparseable falls back to off, with a warning in the log,
        rather than raising on a page load. (Odoo 19 spelled this
        ``str2bool(get_param(...), False)``; 20 removed ``get_param`` for typed
        getters that parse the text the same way.)
        """
        result = super().session_info()
        result[SHOW_NAME_PARAM] = (
            self.env["ir.config_parameter"].sudo().get_bool(SHOW_NAME_PARAM, False)
        )
        return result
