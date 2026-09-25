# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

{
    "name": "Multiple Contact Emails",
    "summary": "Assign multiple email addresses to a contact, and Odoo matches mail from all of them",
    "version": "19.0.1.2.0",
    "author": "Valencia Makers",
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
    "images": ["static/description/cover.png"],
}
