# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

{
    "name": "Website Multi-Day Slots",
    "summary": "Show the start and end day of a multi-day slot when a visitor picks it",
    "version": "19.0.1.0.1",
    "author": "Valencia Makers",
    # LGPL-3, as vmk_event_slot_multiday is: see its README.
    "license": "LGPL-3",
    "category": "Marketing/Events",
    "depends": ["vmk_event_slot_multiday", "website_event"],
    # Odoo installs an auto_install module only once every dependency is
    # present, so a backend-only database never sees this one, and adding
    # the Website Events app later pulls it in without anyone going looking.
    "auto_install": True,
    "assets": {
        "web.assets_frontend": [
            "vmk_website_event_slot_multiday/static/src/interactions/*.js",
        ],
    },
    "installable": True,
    "application": False,
}
