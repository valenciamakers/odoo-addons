# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

{
    "name": "Language Sequence",
    "summary": "Reorder languages manually instead of alphabetically",
    "version": "18.0.1.1.0",
    "author": "Valencia Makers",
    "license": "LGPL-3",
    "category": "Website/Website",
    "depends": ["http_routing"],
    "data": ["views/res_lang_views.xml"],
    "assets": {
        "web.assets_tests": [
            "vmk_language_sequence/static/tests/tours/**/*",
        ],
    },
    "post_init_hook": "seed_language_sequence",
    "images": ["static/description/cover.png"],
    "installable": True,
    "application": False,
}
