# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from datetime import timedelta

from odoo import fields
from odoo.tests import TransactionCase, tagged

from odoo.addons.vmk_event_registration_deadline.models.res_config_settings import (
    DEADLINE_PARAM,
    ENABLED_PARAM,
)


@tagged("post_install", "-at_install")
class TestRegistrationDeadline(TransactionCase):
    """Core sells until an event ends. This sells until it starts."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.now = fields.Datetime.now()
        # The feature is off until somebody turns it on, so most of what
        # follows has to turn it on first.
        cls._enable(cls.env)

    @staticmethod
    def _enable(env, on=True):
        env["ir.config_parameter"].sudo().set_param(ENABLED_PARAM, "True" if on else "False")

    def _event(self, starts_in_hours, length_hours=8, **extra):
        begin = self.now + timedelta(hours=starts_in_hours)
        return self.env["event.event"].create(
            dict(
                {
                    "name": "Intro to 3D Printing",
                    "date_tz": "Europe/Madrid",
                    "date_begin": begin,
                    "date_end": begin + timedelta(hours=length_hours),
                },
                **extra,
            )
        )

    def _set_default(self, hours):
        self.env["ir.config_parameter"].sudo().set_param(DEADLINE_PARAM, hours)

    def test_the_feature_is_off_until_enabled(self):
        """Installing the module must not change how anything sells."""
        self._enable(self.env, False)
        event = self._event(starts_in_hours=-1)
        self.assertGreater(event.date_end, self.now, "core would keep this open")
        self.assertTrue(event.event_registrations_open)

    def test_an_event_with_its_own_deadline_needs_no_global_switch(self):
        """The switch means "by default"; an event that sets one has opted in."""
        self._enable(self.env, False)
        event = self._event(starts_in_hours=-1, vmk_deadline_custom=True, vmk_deadline_hours=0)
        self.assertFalse(event.event_registrations_open)

    def test_an_event_yet_to_start_is_open(self):
        self.assertTrue(self._event(starts_in_hours=48).event_registrations_open)

    def test_an_event_underway_is_closed(self):
        """Core would keep this open: its date_end is still ahead."""
        event = self._event(starts_in_hours=-1)
        self.assertGreater(event.date_end, self.now, "the event has not ended")
        self.assertFalse(event.event_registrations_open)

    def test_the_global_deadline_applies(self):
        self._set_default(24)
        self.assertFalse(self._event(starts_in_hours=12).event_registrations_open)
        self.assertTrue(self._event(starts_in_hours=36).event_registrations_open)

    def test_an_event_may_override_the_global_deadline(self):
        self._set_default(24)
        event = self._event(starts_in_hours=12, vmk_deadline_custom=True, vmk_deadline_hours=2)
        self.assertTrue(event.event_registrations_open)

    def test_an_override_of_zero_closes_at_the_start(self):
        """Zero is a real setting, which is why the boolean exists."""
        self._set_default(24)
        event = self._event(starts_in_hours=1, vmk_deadline_custom=True, vmk_deadline_hours=0)
        self.assertTrue(event.event_registrations_open)
        past = self._event(starts_in_hours=-1, vmk_deadline_custom=True, vmk_deadline_hours=0)
        self.assertFalse(past.event_registrations_open)

    def test_a_ticket_registration_end_wins(self):
        """A date somebody typed is a deliberate choice to sell late."""
        event = self._event(starts_in_hours=-1)
        self.env["event.event.ticket"].create(
            {
                "name": "Standard",
                "event_id": event.id,
                "end_sale_datetime": self.now + timedelta(days=1),
            }
        )
        event.invalidate_recordset()
        self.assertTrue(event.event_registrations_open)

    def test_a_ticket_without_an_end_does_not_win(self):
        event = self._event(starts_in_hours=-1)
        self.env["event.event.ticket"].create({"name": "Standard", "event_id": event.id})
        event.invalidate_recordset()
        self.assertFalse(event.event_registrations_open)
