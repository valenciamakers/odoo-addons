# Copyright 2026 Valencia Makers, SL
# License MIT (https://opensource.org/licenses/MIT).

{
    "name": "Language Systray",
    "summary": "Switch your own backend language from a systray dropdown",
    "version": "19.0.1.0.0",
    "author": "Valencia Makers, SL",
    "license": "Other OSI approved licence",  # MIT; see LICENSE
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
