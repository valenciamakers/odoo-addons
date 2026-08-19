# Copyright 2026 Valencia Makers, SL
# License AGPL-3 (https://www.gnu.org/licenses/agpl-3.0.html).

{
    "name": "Language Metadata Protection",
    "summary": "Stop Odoo updates reverting your edits to language metadata",
    "version": "19.0.1.1.0",
    "author": "Valencia Makers, SL",
    "license": "AGPL-3",
    "category": "Technical",
    "depends": ["base"],
    "data": ["views/res_lang_views.xml"],
    "post_init_hook": "protect_enabled_languages",
    "installable": True,
    "application": False,
}
