# Copyright 2026 Valencia Makers, SL
# License MIT (https://opensource.org/licenses/MIT).

{
    "name": "Language Sequence",
    "summary": "Order enabled languages by hand instead of alphabetically",
    "version": "19.0.1.0.0",
    "author": "Valencia Makers, SL",
    "license": "Other OSI approved licence",  # MIT; see LICENSE
    "category": "Website/Website",
    "depends": ["website"],
    "data": ["views/res_lang_views.xml"],
    "post_init_hook": "seed_language_sequence",
    "installable": True,
    "application": False,
}
