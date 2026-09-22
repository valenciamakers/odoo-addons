# Copyright 2026 Valencia Makers, SL
# License AGPL-3 (https://www.gnu.org/licenses/agpl-3.0.html).

{
    "name": "Event Registration Deadline",
    "summary": "Stop selling registrations when an event starts, or a set time before",
    "version": "19.0.1.0.0",
    "author": "Valencia Makers, SL",
    "license": "AGPL-3",
    "category": "Marketing/Events",
    # website_event, not event: half the rule lives in `_filter_open_slots`,
    # which that module defines. See README.md.
    "depends": ["website_event"],
    "data": [
        "views/res_config_settings_views.xml",
        "views/event_event_views.xml",
    ],
    "installable": True,
    "application": False,
}
