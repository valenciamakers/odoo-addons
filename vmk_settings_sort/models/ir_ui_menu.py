# Copyright 2026 Valencia Makers, SL
# License MIT (https://opensource.org/licenses/MIT).

from odoo import api, models

from .sort_key import sorted_children

# Settings -> Technical. Resolved by xmlid on purpose: `mail` ships a second
# menu called "Technical" under Discuss, so matching on the name would reorder
# the wrong one as well.
TECHNICAL_MENU = "base.menu_custom"


class IrUiMenu(models.Model):
    _inherit = "ir.ui.menu"

    @api.model
    def load_menus(self, debug):
        """Order the groupings inside the Technical menu, and nothing below them.

        Those groupings -- Actions, Database Structure, Email, Security and the
        rest -- carry colliding sequences in stock: three sit on 10, two on 3,
        two on 5, two on 30. Ties break by `id`, which is install order, so the
        list comes out in an order that is arbitrary and differs per database.

        Only the immediate children are sorted. What sits inside each grouping
        is a deliberate arrangement by whoever wrote it, and alphabetising that
        would be a loss.

        Technical carries `groups="base.group_no_one"`, so it reaches the
        payload only when the session is in developer mode. `sorted_children`
        hands the payload back untouched when it is absent, which is the
        ordinary case.
        """
        menus = super().load_menus(debug)
        technical = self.env.ref(TECHNICAL_MENU, raise_if_not_found=False)
        if not technical:
            return menus
        # Shallow copies inside, never an in-place sort: `super()` is ormcached,
        # so its return value is shared between requests. `vmk_apps_menu_sort`
        # copies the same way for the root menus, and the two compose, each
        # rewriting a different key of the payload.
        return sorted_children(menus, technical.id)
