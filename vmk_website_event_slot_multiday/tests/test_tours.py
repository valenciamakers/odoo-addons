# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from datetime import date, timedelta

from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestTours(HttpCase):
    """The registration modal of the public event page, in a browser.

    Core prints a slot's end as a time alone. The patch under test adds the
    end's date when the slot ends on another day, so the tour checks the
    line a visitor reads. The event is in New York and the browser in UTC, so
    a line formatted in the visitor's zone would put the slot a day out.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # The next Friday at least two months away, so the slots are still in
        # the future whenever the suite runs: visitors are offered only those.
        friday = date.today() + timedelta(days=60)
        friday += timedelta(days=(4 - friday.weekday()) % 7)
        cls.friday = friday
        cls.sunday = friday + timedelta(days=2)
        cls.event = cls.env["event.event"].create(
            {
                "name": "Weekend Workshop",
                "date_tz": "America/New_York",
                "date_begin": f"{friday - timedelta(days=7)} 04:00:00",
                "date_end": f"{friday + timedelta(days=14)} 20:00:00",
                "is_multi_slots": True,
                "website_published": True,
                "event_ticket_ids": [(0, 0, {"name": "Standard"})],
            }
        )
        slots = cls.env["event.slot"]
        cls.weekend = slots.create(
            {
                "event_id": cls.event.id,
                "date": cls.friday,
                "start_hour": 18.0,
                "end_hour": 13.0,
                "vmk_end_date": cls.sunday,
            }
        )
        cls.evening = slots.create(
            {
                "event_id": cls.event.id,
                "date": cls.friday + timedelta(days=7),
                "start_hour": 18.0,
                "end_hour": 20.0,
            }
        )

    def _url(self, slot, start, end=None):
        """The event page, with what the tour should expect to read in its fragment.

        The weekday is English whatever the tour's language: the test
        browser is, and so are these tests, as core's website_event ones.
        """
        url = f"{self.event.website_url}#slot={slot.id}&from={start:%a},{start.day}"
        return url + (f"&to={end:%a},{end.day}" if end else "")

    def test_multiday_slot_names_both_days(self):
        self.assertEqual(self.weekend.vmk_end_day_offset, 2)
        self.start_tour(
            self._url(self.weekend, self.friday, self.sunday),
            "vmk_website_event_slot_multiday_multiday_slot",
            login=None,
        )

    def test_one_day_slot_keeps_cores_line(self):
        self.start_tour(
            self._url(self.evening, self.friday + timedelta(days=7)),
            "vmk_website_event_slot_multiday_one_day_slot",
            login=None,
        )
