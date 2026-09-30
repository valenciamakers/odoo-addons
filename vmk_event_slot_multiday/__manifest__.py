# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

{
    "name": "Multi-Day Event Slots",
    "summary": "Allow event slots to span multiple days",
    "version": "20.0.1.0.0",
    "author": "Valencia Makers",
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
        "web.assets_tests": [
            "vmk_event_slot_multiday/static/tests/tours/**/*",
        ],
    },
    "images": ["static/description/cover.png"],
    "installable": True,
    "application": False,
}
