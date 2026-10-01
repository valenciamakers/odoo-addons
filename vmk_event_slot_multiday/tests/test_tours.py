# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import fields
from odoo.tests import HttpCase, tagged


class SlotTourFixture:
    """An event in New York with a slot calendar, for the tours below.

    The event is in New York and the test browser in UTC, so a widget that
    showed the viewer's own time instead of the event's would store the wrong
    hours. October 2026 is summer time there, UTC-4.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.event = cls.env["event.event"].create(
            {
                "name": "Weekend Workshop",
                "date_tz": "America/New_York",
                # 1 to 31 October, New York time. The slot calendar opens on
                # the month nearest to today within these dates, so on
                # October whatever day the suite runs.
                "date_begin": "2026-10-01 04:00:00",
                "date_end": "2026-11-01 02:00:00",
                "is_multi_slots": True,
            }
        )

    def _slot(self, **values):
        return self.env["event.slot"].create(
            dict(
                {
                    "event_id": self.event.id,
                    "date": "2026-10-09",
                    "start_hour": 18.0,
                    "end_hour": 20.0,
                },
                **values,
            )
        )

    def _event_url(self):
        return f"/odoo/action-event.action_event_view/{self.event.id}"


@tagged("post_install", "-at_install")
class TestTours(SlotTourFixture, HttpCase):
    """The slot range widget, driven in a browser, on a desktop screen."""

    def test_edit_a_slot_range_through_the_picker(self):
        slot = self._slot()
        self.start_tour(
            f"/odoo/event.slot/{slot.id}", "vmk_event_slot_multiday_edit_range", login="admin"
        )
        slot.invalidate_recordset()
        self.assertEqual(slot.date, fields.Date.to_date("2026-10-09"))
        self.assertEqual(slot.start_hour, 18.0)
        self.assertEqual(slot.end_hour, 13.0)
        self.assertEqual(slot.vmk_end_day_offset, 2)
        self.assertEqual(slot.vmk_end_date, fields.Date.to_date("2026-10-11"))
        # 18:00 and 13:00 in New York, four hours behind UTC.
        self.assertEqual(slot.start_datetime, fields.Datetime.to_datetime("2026-10-09 22:00:00"))
        self.assertEqual(slot.end_datetime, fields.Datetime.to_datetime("2026-10-11 17:00:00"))

    def test_multi_create_one_slot_per_selected_day(self):
        calendar = self.env["event.slot"].get_view(view_type="calendar")["arch"]
        if "multi_create_view" not in calendar:
            self.skipTest("Another module turned off the slot calendar's multi-create")
        self.start_tour(
            self._event_url(), "vmk_event_slot_multiday_calendar_multi_create", login="admin"
        )
        slots = self.event.event_slot_ids.sorted("date")
        self.assertEqual(
            slots.mapped("date"),
            [fields.Date.to_date("2026-10-13"), fields.Date.to_date("2026-10-14")],
        )
        for slot in slots:
            self.assertEqual(slot.start_hour, 10.0)
            self.assertEqual(slot.end_hour, 12.5)
            self.assertEqual(slot.vmk_end_day_offset, 0)
            self.assertEqual(slot.vmk_end_date, slot.date)


@tagged("post_install", "-at_install")
class TestSmallScreenTours(SlotTourFixture, HttpCase):
    """The slot calendar on a phone-sized screen.

    Core's calendar offers two ways to make a slot. On a desktop screen a
    click only selects days, for the Add button to turn into slots; the New
    Slot dialog, built on the slot form this module changes, opens only when
    the screen is small, so that is where the range widget has to be tried
    inside a dialog.
    """

    browser_size = "480,900"

    def test_new_multiday_slot_from_the_calendar(self):
        self.start_tour(self._event_url(), "vmk_event_slot_multiday_calendar_new", login="admin")
        slot = self.event.event_slot_ids
        self.assertEqual(len(slot), 1)
        self.assertEqual(slot.date, fields.Date.to_date("2026-10-16"))
        self.assertEqual(slot.start_hour, 17.5)
        self.assertEqual(slot.end_hour, 11.25)
        self.assertEqual(slot.vmk_end_day_offset, 2)
        self.assertEqual(slot.start_datetime, fields.Datetime.to_datetime("2026-10-16 21:30:00"))
        self.assertEqual(slot.end_datetime, fields.Datetime.to_datetime("2026-10-18 15:15:00"))
