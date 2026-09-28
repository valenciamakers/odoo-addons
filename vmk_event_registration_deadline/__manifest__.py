# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

{
    "name": "Event Registration Deadline",
    "summary": "Allow registration only until an event starts, or a set time in advance",
    "version": "18.0.1.0.0",
    "author": "Valencia Makers",
    "license": "LGPL-3",
    "category": "Marketing/Events",
    # website_event, not event: `event_registrations_open` is a plain `event`
    # field, but the only place it visibly does anything is the website's
    # registration templates. See README.md.
    "depends": ["website_event"],
    "data": [
        "views/res_config_settings_views.xml",
        "views/event_event_views.xml",
    ],
    "images": ["static/description/cover.png"],
    "installable": True,
    "application": False,
}
