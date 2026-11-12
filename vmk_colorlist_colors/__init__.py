# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from . import models
from .models.vmk_colorlist_color import DARK_URL, LIGHT_URL


def _uninstall_hook(env):
    """Take the generated stylesheets out of the bundles. They are records the
    module made at run time, not its data, so uninstalling would otherwise
    leave Odoo with the custom colors and nothing to change them back."""
    env["ir.asset"].sudo().search([("path", "in", [LIGHT_URL, DARK_URL])]).unlink()
    env["ir.attachment"].sudo().search([("url", "in", [LIGHT_URL, DARK_URL])]).unlink()
