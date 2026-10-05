# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

{
    "name": "Apps Menu Sort",
    "summary": "Alphabetical order for the apps menu, with Apps and Settings at the end",
    "version": "18.0.1.1.0",
    "author": "Valencia Makers",
    "license": "LGPL-3",
    "category": "Technical",
    "depends": ["base"],
    "data": ["data/ir_actions_server.xml"],
    "assets": {
        "web.assets_tests": ["vmk_apps_menu_sort/static/tests/tours/**/*"],
    },
    "images": ["static/description/cover.png"],
    "installable": True,
    "application": False,
}
