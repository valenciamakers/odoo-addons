# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from datetime import datetime, time

import pytz
from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.tests import HttpCase, tagged

NEW_YORK = pytz.timezone("America/New_York")


@tagged("post_install", "-at_install")
class TestTours(HttpCase):
    """The slot range widget, driven in a browser.

    The event is in New York and the test browser in UTC, so a widget that
    showed the viewer's own time instead of the event's would store the wrong
    hours.

    The event takes up the whole of the month the suite runs in, and the
    tours pick days of it by number: the slot calendar and the range picker
    open on the month nearest to today within the event's dates, so on this
    one. Fixed dates passed only in the month they were written in.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.month = fields.Date.today().replace(day=1)
        cls.event = cls.env["event.event"].create(
            {
                "name": "Weekend Workshop",
                "date_tz": "America/New_York",
                "date_begin": cls._utc(cls.month, 0),
                "date_end": cls._utc(cls.month + relativedelta(months=1), 0),
                "is_multi_slots": True,
            }
        )

    @classmethod
    def _day(cls, number):
        return cls.month.replace(day=number)

    @classmethod
    def _utc(cls, day, hour, minute=0):
        """A New York wall-clock time on `day`, as the UTC Odoo stores, in
        summer or winter time alike."""
        local = NEW_YORK.localize(datetime.combine(day, time(hour, minute)))
        return local.astimezone(pytz.utc).replace(tzinfo=None)

    def _slot(self, **values):
        return self.env["event.slot"].create(
            dict(
                {
                    "event_id": self.event.id,
                    "date": self._day(9),
                    "start_hour": 18.0,
                    "end_hour": 20.0,
                },
                **values,
            )
        )

    def _event_url(self):
        return f"/odoo/action-event.action_event_view/{self.event.id}"

    def test_edit_a_slot_range_through_the_picker(self):
        slot = self._slot()
        self.start_tour(
            f"/odoo/event.slot/{slot.id}", "vmk_event_slot_multiday_edit_range", login="admin"
        )
        slot.invalidate_recordset()
        self.assertEqual(slot.date, self._day(9))
        self.assertEqual(slot.start_hour, 18.0)
        self.assertEqual(slot.end_hour, 13.0)
        self.assertEqual(slot.vmk_end_day_offset, 2)
        self.assertEqual(slot.vmk_end_date, self._day(11))
        # 18:00 and 13:00 in New York, four or five hours behind UTC.
        self.assertEqual(slot.start_datetime, self._utc(self._day(9), 18))
        self.assertEqual(slot.end_datetime, self._utc(self._day(11), 13))

    def test_new_multiday_slot_from_the_calendar(self):
        self.start_tour(self._event_url(), "vmk_event_slot_multiday_calendar_new", login="admin")
        slot = self.event.event_slot_ids
        self.assertEqual(len(slot), 1)
        self.assertEqual(slot.date, self._day(16))
        self.assertEqual(slot.start_hour, 17.5)
        self.assertEqual(slot.end_hour, 11.25)
        self.assertEqual(slot.vmk_end_day_offset, 2)
        self.assertEqual(slot.start_datetime, self._utc(self._day(16), 17, 30))
        self.assertEqual(slot.end_datetime, self._utc(self._day(18), 11, 15))

    def test_multi_create_one_slot_per_selected_day(self):
        calendar = self.env["event.slot"].get_view(view_type="calendar")["arch"]
        if "multi_create_view" not in calendar:
            self.skipTest("Another module turned off the slot calendar's multi-create")
        self.start_tour(
            self._event_url(), "vmk_event_slot_multiday_calendar_multi_create", login="admin"
        )
        slots = self.event.event_slot_ids.sorted("date")
        self.assertEqual(slots.mapped("date"), [self._day(13), self._day(14)])
        for slot in slots:
            self.assertEqual(slot.start_hour, 10.0)
            self.assertEqual(slot.end_hour, 12.5)
            self.assertEqual(slot.vmk_end_day_offset, 0)
            self.assertEqual(slot.vmk_end_date, slot.date)
