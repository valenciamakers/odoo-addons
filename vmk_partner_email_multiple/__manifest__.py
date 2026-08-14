# Copyright 2026 Valencia Makers, SL
# License MIT (https://opensource.org/licenses/MIT).

{
    "name": "Multiple Contact Emails",
    "summary": "Several email addresses per contact, matched by Odoo's own machinery",
    "version": "19.0.1.0.0",
    "author": "Valencia Makers, SL",
    "license": "Other OSI approved licence",  # MIT; see LICENSE
    "category": "Productivity/Discuss",
    "depends": ["mail"],
    "data": [
        "security/ir.model.access.csv",
        "views/res_partner_views.xml",
    ],
    "installable": True,
    "application": False,
}
