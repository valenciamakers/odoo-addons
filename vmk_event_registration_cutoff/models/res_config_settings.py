# Copyright 2026 Valencia Makers, SL
# License AGPL-3 (https://www.gnu.org/licenses/agpl-3.0.html).

from odoo import fields, models

# The key is the module's own, not `event.`, so a future core setting cannot
# collide with it.
CUTOFF_PARAM = "vmk_event_registration_cutoff.hours"


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    vmk_registration_cutoff_hours = fields.Float(
        string="Close Registration Before Start",
        config_parameter=CUTOFF_PARAM,
        help="How long before an event starts registration closes. "
        "Zero closes it as the event begins. An event can override this.",
    )
