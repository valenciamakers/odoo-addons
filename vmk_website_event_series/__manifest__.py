# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

{
    "name": "Event Series (Website)",
    "summary": "A page for each event series on the website, listing its upcoming dates",
    "version": "20.0.1.0.0",
    "author": "Valencia Makers",
    "license": "LGPL-3",
    "category": "Marketing/Events",
    "depends": ["vmk_event_series", "website_event"],
    # Odoo installs an auto_install module once every dependency is present,
    # so adding the Events app to a database with series brings this along.
    "auto_install": True,
    "data": [
        "security/ir.access.csv",
        "views/vmk_event_series_views.xml",
        "views/vmk_event_series_templates.xml",
        "views/event_templates.xml",
    ],
    "assets": {
        "web.assets_tests": [
            "vmk_website_event_series/static/tests/tours/**/*",
        ],
    },
    "installable": True,
    "application": False,
}
