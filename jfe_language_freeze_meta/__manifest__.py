# Copyright 2026 Valencia Makers, SL
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Language Metadata Protection",
    "summary": "Stop Odoo updates reverting your edits to language metadata",
    "version": "19.0.1.0.0",
    "author": "Valencia Makers, SL",
    "license": "LGPL-3",
    "category": "Technical",
    "depends": ["base"],
    "data": ["views/res_lang_views.xml"],
    "post_init_hook": "protect_enabled_languages",
    "installable": True,
    "application": False,
}
