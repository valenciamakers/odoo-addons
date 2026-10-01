# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from datetime import timedelta

import pytz

from odoo import fields
from odoo.tests import HttpCase, tagged

from odoo.addons.vmk_event_registration_deadline.models.res_config_settings import (
    DEADLINE_PARAM,
    ENABLED_PARAM,
)

TOUR = "vmk_event_registration_deadline_"


@tagged("post_install", "-at_install")
class TestTours(HttpCase):
    """What a visitor is offered, and how an organiser sets the rule, in a browser.

    Every date is relative to the moment the suite runs. The global deadline
    is 24 hours, so an event starting in 12 hours is past it and one starting
    in 36 is not, with neither near to starting or ending.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.now = fields.Datetime.now()
        cls._set_global(True, 24.0)

    @classmethod
    def _set_global(cls, enabled, hours):
        params = cls.env["ir.config_parameter"].sudo()
        params.set_param(ENABLED_PARAM, "True" if enabled else "False")
        params.set_param(DEADLINE_PARAM, hours)

    @classmethod
    def _event(cls, name, starts_in_hours, length_hours=8, **extra):
        begin = cls.now + timedelta(hours=starts_in_hours)
        return cls.env["event.event"].create(
            dict(
                {
                    "name": name,
                    "date_tz": "Europe/Madrid",
                    "date_begin": begin,
                    "date_end": begin + timedelta(hours=length_hours),
                    "website_published": True,
                },
                **extra,
            )
        )

    @classmethod
    def _slot(cls, event, when):
        """A slot at a given moment, as the date and local hours core wants.

        `start_hour` is a clock time in the event's timezone, not an offset.
        """
        local = pytz.utc.localize(when).astimezone(pytz.timezone(event.date_tz))
        hour = local.hour + local.minute / 60.0
        return cls.env["event.slot"].create(
            {
                "event_id": event.id,
                "date": local.date(),
                "start_hour": hour,
                "end_hour": min(hour + 1.0, 23.99),
            }
        )

    def _visit(self, event, tour):
        self.start_tour(event.website_url, TOUR + tour, login=None)

    def _slots_event(self, name, *hours_ahead):
        """A multi-slot event with a slot each so many hours from now."""
        event = self._event(name, 0, length_hours=24 * 10, is_multi_slots=True)
        slots = self.env["event.slot"]
        for hours in hours_ahead:
            slots |= self._slot(event, self.now + timedelta(hours=hours))
        event.invalidate_recordset()
        return event, slots

    # A visitor on the event page

    def test_past_the_deadline_registration_is_not_offered(self):
        soon = self._event("Starts In Twelve Hours", 12)
        self.assertGreater(soon.date_end, self.now, "the event has not ended")
        self.assertFalse(soon.event_registrations_open)
        self._visit(soon, "closed")

    def test_underway_registration_is_not_offered(self):
        """Core alone would keep this on sale, as its end is still ahead."""
        underway = self._event("Began An Hour Ago", -1)
        self._visit(underway, "closed")

    def test_before_the_deadline_registration_is_offered(self):
        far = self._event("Starts In Thirty Six Hours", 36)
        self.assertTrue(far.event_registrations_open)
        self._visit(far, "open")

    def test_an_event_may_loosen_the_deadline(self):
        plain = self._event("Plain Twelve Hours", 12)
        loose = self._event(
            "Loose Twelve Hours", 12, vmk_deadline_custom=True, vmk_deadline_hours=2.0
        )
        self._visit(plain, "closed")
        self._visit(loose, "open")

    def test_an_event_may_tighten_the_deadline(self):
        plain = self._event("Plain Thirty Six Hours", 36)
        tight = self._event(
            "Tight Thirty Six Hours", 36, vmk_deadline_custom=True, vmk_deadline_hours=48.0
        )
        self._visit(plain, "open")
        self._visit(tight, "closed")

    def test_an_event_with_its_own_deadline_ignores_the_global_switch(self):
        self._set_global(False, 24.0)
        plain = self._event("Plain With Switch Off", 12)
        own = self._event("Own With Switch Off", 12, vmk_deadline_custom=True, vmk_deadline_hours=48.0)
        self._visit(plain, "open")
        self._visit(own, "closed")

    # A visitor choosing a slot

    def _slot_url(self, event, soon, later):
        return f"{event.website_url}#soon={soon.id or 0}&later={later.id}"

    def test_a_slot_past_the_deadline_is_not_offered(self):
        event, (soon, later) = self._slots_event("Two Slots", 12, 24 * 5)
        self.assertTrue(event.event_registrations_open)
        self.start_tour(self._slot_url(event, soon, later), TOUR + "slots", login=None)

    def test_a_slot_is_offered_while_the_deadline_is_off(self):
        """The control: core alone still offers a slot twelve hours away."""
        self._set_global(False, 24.0)
        event, (soon, later) = self._slots_event("Two Slots Switch Off", 12, 24 * 5)
        self.start_tour(self._slot_url(event, soon, later), TOUR + "slots_offered", login=None)

    def test_every_slot_past_the_deadline_closes_the_event(self):
        """The control is the test above: one slot still ahead keeps Register."""
        event, _slots = self._slots_event("All Slots Soon", 6, 12)
        self.assertFalse(event.event_registrations_open)
        self._visit(event, "closed")

    # An organiser in the backend

    def test_the_setting_is_saved_from_settings(self):
        self._set_global(False, 0.0)
        event = self._event("Starts In Two Hours", 2)
        self.assertTrue(event.event_registrations_open)
        self.start_tour("/odoo/action-event.action_event_configuration", TOUR + "settings", login="admin")
        params = self.env["ir.config_parameter"].sudo()
        self.assertEqual(params.get_param(ENABLED_PARAM), "True")
        self.assertEqual(float(params.get_param(DEADLINE_PARAM)), 3.5)
        event.invalidate_recordset()
        self.assertFalse(event.event_registrations_open, "inside the 3:30 deadline now")

    def test_the_event_deadline_is_saved_from_the_form(self):
        event = self._event("Starts In Two Hours Again", 2)
        self.assertFalse(event.event_registrations_open, "inside the global 24 hours")
        self.assertFalse(event.vmk_deadline_custom)
        self.start_tour(
            f"/odoo/action-event.action_event_view/{event.id}", TOUR + "event_form", login="admin"
        )
        event.invalidate_recordset()
        self.assertTrue(event.vmk_deadline_custom)
        self.assertEqual(event.vmk_deadline_hours, 1.0)
        self.assertTrue(event.event_registrations_open, "its own hour wins over the 24")
