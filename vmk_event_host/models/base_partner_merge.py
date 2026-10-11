# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import models


class BasePartnerMergeAutomaticWizard(models.TransientModel):
    _inherit = "base.partner.merge.automatic.wizard"

    def _merge(self, partner_ids, dst_partner=None, extra_checks=True):
        """Leave the surviving contact with one host line per event.

        ``_update_foreign_keys`` (base/wizard/base_partner_merge.py) re-points
        ``vmk_event_host.partner_id`` with one bulk ``UPDATE`` that compares no
        values, so an event two merged contacts both hosted holds the survivor
        twice, unseen by ``_check_partner_unique``. The destination cannot be
        read before ``super()``: when the wizard passes none, core picks it
        itself. So every candidate is captured, and the survivor asked for after.
        """
        partners = self.env["res.partner"].browse(partner_ids).exists()
        result = super()._merge(partner_ids, dst_partner=dst_partner, extra_checks=extra_checks)
        survivor = partners.exists()
        if len(survivor) == 1:
            self.env["vmk.event.host"]._vmk_dedupe(survivor)
        return result
