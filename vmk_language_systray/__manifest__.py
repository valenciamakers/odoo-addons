# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

{
    "name": "Backend Language Menu",
    "summary": "Switch your own backend language from a systray dropdown",
    "version": "19.0.1.1.1",
    "author": "Valencia Makers",
    "license": "LGPL-3",
    "category": "Technical",
    "depends": ["web"],
    "assets": {
        "web.assets_backend": [
            "vmk_language_systray/static/src/**/*",
        ],
    },
    "installable": True,
    "application": False,
}
