# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    """Drop the additional rows that repeat their contact's primary address.

    Until 19.0.1.3.2 editing a contact's email to an address already in its
    list left that row in place; ``res.partner.write`` now drops it, but only
    on the next edit, so rows left by earlier edits are cleared here, through
    the same method.
    """
    cr.execute(
        """
        SELECT DISTINCT e.partner_id
          FROM vmk_partner_email e
          JOIN res_partner p ON p.id = e.partner_id
         WHERE e.email_normalized IS NOT NULL
           AND e.email_normalized = p.email_normalized
        """
    )
    partner_ids = [row[0] for row in cr.fetchall()]
    if partner_ids:
        env = api.Environment(cr, SUPERUSER_ID, {})
        env["res.partner"].browse(partner_ids)._vmk_drop_rows_equal_to_primary()
