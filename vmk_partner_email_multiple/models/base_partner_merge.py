# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import models


class BasePartnerMergeAutomaticWizard(models.TransientModel):
    _inherit = "base.partner.merge.automatic.wizard"

    def _merge(self, partner_ids, dst_partner=None, extra_checks=True):
        """Keep the merged-away contacts' addresses instead of dropping them.

        Most of the merge already does the right thing. ``_update_foreign_keys``
        re-points every foreign key to ``res_partner`` in raw SQL discovered from
        the schema (base/wizard/base_partner_merge.py:292-299), so this module's
        child rows follow the surviving contact with no code from us.

        The gap is ``_update_values`` (:314-364): it skips o2m/m2m and computed
        fields, and for plain fields takes the last truthy value with the
        destination last -- so the destination's ``email`` wins and every other
        contact's address is simply lost. That single gap is the feature.

        The addresses have to be captured before ``super()``, because the source
        contacts are unlinked at :444. The *destination* cannot be captured that
        early: when the wizard passes none, core picks it itself at :415-421. So
        capture every candidate's address, then ask which record survived.

        The migration can also leave a genuine duplicate behind -- see
        ``_vmk_dedupe_emails`` on ``res.partner`` and README.md -- so every
        successful two-or-more-contact merge is followed by a dedupe pass, not
        only the ones with a primary address to absorb.

        The same-email guard at :413 is deliberately left alone. It refuses a
        merge when the contacts differ by email -- which is every case this module
        exists for -- but admins are exempted at :390-391, so it does not bite in
        practice. See README.md.
        """
        partners = self.env["res.partner"].browse(partner_ids).exists()
        absorbed = [partner.email for partner in partners if partner.email]

        result = super()._merge(partner_ids, dst_partner=dst_partner, extra_checks=extra_checks)

        survivor = partners.exists()
        if len(survivor) != 1:
            # Core bailed out (fewer than two contacts).
            return result
        if absorbed:
            survivor._vmk_absorb_emails(absorbed)
        survivor._vmk_dedupe_emails()
        return result
