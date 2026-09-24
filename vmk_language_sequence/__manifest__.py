# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

{
    "name": "Language Sequence",
    "summary": "Order enabled languages by hand instead of alphabetically",
    "version": "19.0.1.1.1",
    "author": "Valencia Makers, SL",
    "license": "LGPL-3",
    "category": "Website/Website",
    "depends": ["website"],
    "data": ["views/res_lang_views.xml"],
    "post_init_hook": "seed_language_sequence",
    "installable": True,
    "application": False,
}
