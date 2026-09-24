# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import fields, models

# The key is the module's own, not `event.`, so a future core setting cannot
# collide with it.
DEADLINE_PARAM = "vmk_event_registration_deadline.hours"
ENABLED_PARAM = "vmk_event_registration_deadline.enabled"


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # Gated by its own boolean, as core gates a feature inside an installed
    # module: `use_event_barcode` eleven lines away in this same settings
    # page, `use_invoice_terms`, `use_google_maps_static_api`. Installing a
    # module should not change how anything sells until somebody says so.
    vmk_registration_deadline_enabled = fields.Boolean(
        string="Registration Deadline",
        config_parameter=ENABLED_PARAM,
        help="Sell tickets only until an event starts, or a set time in "
        "advance. Set to 00:00 to end registration at the event start time.",
    )
    # No `help`: a `setting` labels its own fields and does not give them the
    # `?` a form label would, so anything written here is never seen. The one
    # detail worth saying, that 00:00 ends registration at the event's start,
    # lives in the help above, which renders as the muted line under the title.
    vmk_registration_deadline_hours = fields.Float(
        string="Time Before Start",
        config_parameter=DEADLINE_PARAM,
    )
