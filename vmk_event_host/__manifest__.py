# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

{
    "name": "Event Hosts",
    "summary": "Record who runs an event, as one or more contacts",
    "version": "19.0.2.2.0",
    "author": "Valencia Makers, SL",
    # LGPL-3 rather than this repo's AGPL-3 default: our own proprietary
    # modules depend on this one, and Odoo's licence compatibility rules
    # forbid a proprietary module depending on AGPL. See README.md.
    "license": "LGPL-3",
    "category": "Marketing/Events",
    "depends": ["event"],
    "data": [
        "security/ir.model.access.csv",
        "security/vmk_event_host_security.xml",
        "views/event_event_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "vmk_event_host/static/src/**/*",
        ],
    },
    "installable": True,
    "application": False,
}
