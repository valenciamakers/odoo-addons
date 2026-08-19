# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

{
    "name": "Multiple Contact Emails",
    "summary": "Several email addresses per contact, matched by Odoo's own machinery",
    "version": "19.0.1.1.1",
    "author": "Valencia Makers, SL",
    "license": "LGPL-3",
    "category": "Productivity/Discuss",
    "depends": ["mail"],
    "data": [
        "security/ir.model.access.csv",
        "views/res_partner_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "vmk_partner_email_multiple/static/src/**/*",
        ],
    },
    "installable": True,
    "application": False,
}
