# Copyright 2026 Valencia Makers, SL
# License AGPL-3 (https://www.gnu.org/licenses/agpl-3.0.html).

from odoo import fields, models

# The key is the module's own, not `event.`, so a future core setting cannot
# collide with it.
CUTOFF_PARAM = "vmk_event_registration_cutoff.hours"
ENABLED_PARAM = "vmk_event_registration_cutoff.enabled"


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # Gated by its own boolean, as core gates a feature inside an installed
    # module: `use_event_barcode` eleven lines away in this same settings
    # page, `use_invoice_terms`, `use_google_maps_static_api`. Installing a
    # module should not change how anything sells until somebody says so.
    vmk_registration_cutoff_enabled = fields.Boolean(
        string="Registration Cutoff",
        config_parameter=ENABLED_PARAM,
        help="Stop selling registrations when an event starts, or a set time before it.",
    )
    vmk_registration_cutoff_hours = fields.Float(
        string="Close Registration Before Start",
        config_parameter=CUTOFF_PARAM,
        help="How long before an event starts registration closes. "
        "Zero closes it as the event begins. An event can override this.",
    )
