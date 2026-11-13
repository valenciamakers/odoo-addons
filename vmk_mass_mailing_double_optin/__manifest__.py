# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

{
    "name": "Double Opt-In for Email Marketing",
    "summary": "Confirm new mailing list subscribers by email, and log every consent change",
    "version": "20.0.1.0.0",
    "author": "Valencia Makers",
    "license": "LGPL-3",
    "category": "Marketing/Email Marketing",
    "depends": ["mass_mailing"],
    "data": [
        "security/ir.access.csv",
        "data/mail_template_data.xml",
        "data/ir_cron_data.xml",
        "views/vmk_mailing_consent_log_views.xml",
        "views/mailing_list_views.xml",
        "views/mailing_contact_views.xml",
        "views/mailing_subscription_templates.xml",
    ],
    "assets": {
        "web.assets_tests": [
            "vmk_mass_mailing_double_optin/static/tests/tours/**/*",
        ],
    },
    "installable": True,
    "application": False,
}
