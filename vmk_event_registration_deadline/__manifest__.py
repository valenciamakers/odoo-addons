# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

{
    "name": "Event Registration Deadline",
    "summary": "Sell tickets only until an event starts, or a set time in advance",
    "version": "19.0.1.0.2",
    "author": "Valencia Makers",
    "license": "LGPL-3",
    "category": "Marketing/Events",
    # website_event, not event: half the rule lives in `_filter_open_slots`,
    # which that module defines. See README.md.
    "depends": ["website_event"],
    "data": [
        "views/res_config_settings_views.xml",
        "views/event_event_views.xml",
    ],
    "images": ["static/description/cover.png"],
    "installable": True,
    "application": False,
}
