# Copyright 2026 Valencia Makers, SL
# License MIT (https://opensource.org/licenses/MIT).

{
    "name": "Language Metadata Protection",
    "summary": "Stop Odoo updates reverting your edits to language metadata",
    "version": "19.0.1.0.0",
    "author": "Valencia Makers, SL",
    "license": "Other OSI approved licence",  # MIT; see LICENSE
    "category": "Technical",
    "depends": ["base"],
    "data": ["views/res_lang_views.xml"],
    "post_init_hook": "protect_enabled_languages",
    "installable": True,
    "application": False,
}
