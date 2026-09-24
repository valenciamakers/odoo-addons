# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

{
    "name": "Multi-Day Event Slots",
    "summary": "Let an event slot run over several days, not only within one",
    "version": "19.0.1.0.0",
    "author": "Valencia Makers, SL",
    # LGPL-3 rather than this repo's AGPL-3 default: our own proprietary
    # vmk_event_sessions is meant to build on it, and Odoo's licence
    # compatibility rules forbid a proprietary module depending on AGPL.
    # See README.md.
    "license": "LGPL-3",
    "category": "Marketing/Events",
    "depends": ["event"],
    "data": [
        "views/event_slot_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "vmk_event_slot_multiday/static/src/fields/*.js",
        ],
    },
    "installable": True,
    "application": False,
}
