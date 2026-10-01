# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

{
    "name": "Event Registration Deadline",
    "summary": "Allow registration only until an event starts, or a set time in advance",
    "version": "20.0.1.1.0",
    "author": "Valencia Makers",
    "license": "LGPL-3",
    "category": "Marketing/Events",
    # website_event, not event: half the rule lives in `_filter_open_slots`,
    # which that module defines. See README.md.
    "depends": ["website_event"],
    "assets": {
        "web.assets_backend": [
            "vmk_event_registration_deadline/static/src/registration_deadline.scss",
        ],
        "web.assets_tests": ["vmk_event_registration_deadline/static/tests/tours/**/*"],
    },
    "data": [
        "views/res_config_settings_views.xml",
        "views/event_event_views.xml",
    ],
    "images": ["static/description/cover.png"],
    "installable": True,
    "application": False,
}
