# Copyright 2026 Valencia Makers, SL
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Language Sequence",
    "summary": "Order enabled languages by hand instead of alphabetically",
    "version": "19.0.1.0.0",
    "author": "Valencia Makers, SL",
    "license": "LGPL-3",
    "category": "Website/Website",
    "depends": ["website"],
    "data": ["views/res_lang_views.xml"],
    "post_init_hook": "seed_language_sequence",
    "installable": True,
    "application": False,
}
