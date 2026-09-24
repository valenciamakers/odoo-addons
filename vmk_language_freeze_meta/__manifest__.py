# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

{
    "name": "Protect Language Edits",
    "summary": "Stop Odoo updates from reverting your edits to language settings",
    "version": "19.0.1.1.1",
    "author": "Valencia Makers",
    "license": "LGPL-3",
    "category": "Technical",
    "depends": ["base"],
    "data": ["views/res_lang_views.xml"],
    "post_init_hook": "protect_enabled_languages",
    "images": ["static/description/cover.png"],
    "installable": True,
    "application": False,
}
