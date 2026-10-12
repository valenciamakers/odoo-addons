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
        twice, unseen by ``_check_partner_unique``. On that event the line that
        was the survivor's own is the one to keep, with its role and position,
        and the merged contact's goes: the merge keeps the survivor's name and
        email the same way. Which lines are whose has to be read before
        ``super()``, since the raw SQL then points them all at the survivor; and
        the destination cannot, because when the wizard passes none core picks
        it itself. So every candidate's lines are captured, and the survivor
        asked for after.
        """
        partners = self.env["res.partner"].browse(partner_ids).exists()
        # As superuser, like core's own bookkeeping in this method (the raw SQL
        # for the foreign keys, and the `.sudo()` searches and writes of
        # `_update_reference_fields_generic`). The wizard is
        # granted to `base.group_partner_manager`, who need no Events group and
        # would get an AccessError on every merge otherwise; and an Events user
        # sees only their own companies' lines, so the dedupe could miss the
        # survivor's duplicates on an event of another company.
        Host = self.env["vmk.event.host"].sudo()
        own_lines = {
            partner.id: Host.search([("partner_id", "=", partner.id)]).ids for partner in partners
        }
        result = super()._merge(partner_ids, dst_partner=dst_partner, extra_checks=extra_checks)
        survivor = partners.exists()
        if len(survivor) == 1:
            Host._vmk_dedupe(survivor, keep=own_lines.get(survivor.id, ()))
        return result
