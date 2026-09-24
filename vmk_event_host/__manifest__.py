# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

{
    "name": "Event Hosts",
    "summary": "Record who runs an event, as one or more contacts",
    "version": "19.0.1.0.2",
    "author": "Valencia Makers",
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
    "images": ["static/description/cover.png"],
    "installable": True,
    "application": False,
}
