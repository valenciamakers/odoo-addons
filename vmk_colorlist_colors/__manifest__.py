# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

{
    "name": "Custom Colors",
    "summary": "Change the colors used for tags, kanban cards, and calendars, and their names",
    "version": "20.0.1.0.0",
    "author": "Valencia Makers",
    "license": "LGPL-3",
    "category": "Technical",
    "depends": ["base_setup"],
    "data": [
        "security/ir.access.csv",
        "data/vmk_colorlist_color_data.xml",
        "views/vmk_colorlist_color_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "vmk_colorlist_colors/static/src/**/*",
        ],
        "web.assets_tests": [
            "vmk_colorlist_colors/static/tests/tours/**/*",
        ],
    },
    "uninstall_hook": "_uninstall_hook",
    "installable": True,
    "application": False,
}
