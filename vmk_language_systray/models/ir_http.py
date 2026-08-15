# Copyright 2026 Valencia Makers, SL
# License MIT (https://opensource.org/licenses/MIT).

from odoo import models
from odoo.tools import str2bool

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
        ``"quick_login": str2bool(IrConfigSudo.get_param('web.quick_login',
        default=True), True)``.

        ``str2bool`` because a system parameter is free-text -- someone typing
        ``true`` or ``1`` in that screen means the same thing as ``True``, and
        anything unparseable falls back to off rather than raising on a page
        load.
        """
        result = super().session_info()
        result[SHOW_NAME_PARAM] = str2bool(
            self.env["ir.config_parameter"].sudo().get_param(SHOW_NAME_PARAM, default=False),
            False,
        )
        return result
