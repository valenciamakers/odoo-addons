# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo.tests import TransactionCase


class PartnerEmailCase(TransactionCase):
    """Behaviour, not ambient state: every test builds the contacts it asserts on."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Partner = cls.env["res.partner"]
        cls.PartnerEmail = cls.env["vmk.partner.email"]
        cls.Wizard = cls.env["base.partner.merge.automatic.wizard"]

        cls.alice = cls.Partner.create(
            {
                "name": "Alice Example",
                "email": "alice@example.com",
                "vmk_email_ids": [
                    (0, 0, {"email": "alice.work@example.com", "label": "work"}),
                    (0, 0, {"email": "noreply@alice-shop.example.com"}),
                ],
            }
        )
