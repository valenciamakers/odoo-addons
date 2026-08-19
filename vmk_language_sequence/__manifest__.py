# Copyright 2026 Valencia Makers, SL
# License AGPL-3 (https://www.gnu.org/licenses/agpl-3.0.html).

{
    "name": "Language Sequence",
    "summary": "Order enabled languages by hand instead of alphabetically",
    "version": "19.0.1.1.0",
    "author": "Valencia Makers, SL",
    "license": "AGPL-3",
    "category": "Website/Website",
    "depends": ["website"],
    "data": ["views/res_lang_views.xml"],
    "post_init_hook": "seed_language_sequence",
    "installable": True,
    "application": False,
}
