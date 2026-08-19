# Copyright 2026 Valencia Makers, SL
# License AGPL-3 (https://www.gnu.org/licenses/agpl-3.0.html).

from odoo import _, api, models


class ResUsersSettings(models.Model):
    _inherit = "res.users.settings"

    @api.model
    def reset_app_grid_order(self):
        """Clear every user's stored app grid order, and report what happened.

        Dragging an icon on the Enterprise app grid stores that user's own order
        in `homemenu_config`, and `home_menu_service.js` then applies it over the
        order this module produces. Clearing it hands those users the module's
        order back; they remain free to drag their own again afterwards.

        Called from a server action an administrator runs deliberately, never on
        install: silently deleting a per-user preference as a side effect of
        installing a module is not something we are willing to ship.
        """
        if "homemenu_config" not in self._fields:
            # Community, or Enterprise without the home menu. Nothing stored, and
            # nothing was overriding this module's order in the first place.
            return self._app_grid_notification(
                _("Nothing to reset: the app grid order is an Odoo Enterprise feature.")
            )
        # Filtered in Python rather than searched with a domain: `homemenu_config`
        # is a `fields.Json`, whose support for comparison operators is not
        # something to depend on. There is at most one record per user, so
        # reading them all costs nothing.
        customised = self.sudo().search([]).filtered("homemenu_config")
        count = len(customised)
        customised.write({"homemenu_config": False})
        return self._app_grid_notification(
            _("Reset the app grid order for %s user(s).", count)
        )

    @api.model
    def _app_grid_notification(self, message):
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {"message": message, "type": "success", "sticky": False},
        }
