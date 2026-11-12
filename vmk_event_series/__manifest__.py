# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

{
    "name": "Event Series",
    "summary": "Group the dates of an event you run again and again into one series",
    "version": "20.0.1.0.0",
    "author": "Valencia Makers",
    "license": "LGPL-3",
    "category": "Marketing/Events",
    "depends": ["event"],
    "data": [
        "security/ir.access.csv",
        "views/vmk_event_series_views.xml",
        "views/event_event_views.xml",
    ],
    "assets": {
        "web.assets_tests": [
            "vmk_event_series/static/tests/tours/**/*",
        ],
    },
    "installable": True,
    "application": False,
}
