# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from datetime import timedelta

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged
from odoo.tools.misc import format_date


@tagged("post_install", "-at_install")
class TestSlotMultiday(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # A weekend in October, Valencia time: summer time, UTC+2.
        cls.event = cls.env["event.event"].create(
            {
                "name": "Weekend Workshop",
                "date_tz": "Europe/Madrid",
                "date_begin": "2026-10-02 06:00:00",
                "date_end": "2026-10-18 20:00:00",
                "is_multi_slots": True,
            }
        )

    def _slot(self, **values):
        return self.env["event.slot"].create(
            dict(
                {"event_id": self.event.id, "date": "2026-10-09", "start_hour": 18.0,
                 "end_hour": 20.0},
                **values,
            )
        )

    def test_a_slot_ends_on_its_own_date_by_default(self):
        """Every slot has an end date; without one given, it is a core slot."""
        slot = self._slot()
        self.assertEqual(slot.vmk_end_date, fields.Date.to_date("2026-10-09"))
        self.assertEqual(slot.end_datetime, fields.Datetime.to_datetime("2026-10-09 18:00:00"))
        # Core's own name, in whatever format the language uses: no second day.
        next_day = format_date(self.env, slot.date + timedelta(days=1), date_format="medium")
        self.assertNotIn(next_day, slot.display_name)

    def test_a_slot_can_run_over_a_weekend(self):
        """Friday 18:00 to Sunday 13:00: the end hour is earlier than the
        start hour, which core refuses within one day and is right across
        three."""
        slot = self._slot(vmk_end_date="2026-10-11", end_hour=13.0)
        self.assertEqual(slot.start_datetime, fields.Datetime.to_datetime("2026-10-09 16:00:00"))
        self.assertEqual(slot.end_datetime, fields.Datetime.to_datetime("2026-10-11 11:00:00"))
        # Both days named, in the language's own format.
        self.assertIn(format_date(self.env, slot.date, date_format="medium"), slot.display_name)
        self.assertIn(
            format_date(self.env, slot.vmk_end_date, date_format="medium"), slot.display_name
        )

    def test_a_one_day_slot_still_ends_after_it_starts(self):
        """Core's own check, untouched for a slot within one day."""
        with self.assertRaises(ValidationError):
            self._slot(start_hour=18.0, end_hour=13.0)

    def test_hours_are_still_hours_across_days(self):
        with self.assertRaises(ValidationError):
            self._slot(vmk_end_date="2026-10-11", end_hour=25.0)

    def test_a_slot_cannot_end_before_it_starts(self):
        slot = self._slot(vmk_end_date="2026-10-11", end_hour=13.0)
        with self.assertRaisesRegex(ValidationError, "cannot end before it starts"):
            slot.write({"vmk_end_date": "2026-10-08"})

    def test_moving_a_multiday_slot_keeps_its_length(self):
        """The weekend moved a week later is still a weekend."""
        slot = self._slot(vmk_end_date="2026-10-11", end_hour=13.0)
        slot.write({"date": "2026-10-16"})
        self.assertEqual(slot.vmk_end_date, fields.Date.to_date("2026-10-18"))
        self.assertEqual(slot.end_datetime, fields.Datetime.to_datetime("2026-10-18 11:00:00"))

    def test_moving_a_one_day_slot_keeps_it_one_day(self):
        """Either way: an end that stayed put when a slot moved earlier once
        turned a one-day slot into a five-day one."""
        slot = self._slot(date="2026-10-17")
        slot.write({"date": "2026-10-13"})
        self.assertEqual(slot.vmk_end_date, fields.Date.to_date("2026-10-13"))
        slot.write({"date": "2026-10-16"})
        self.assertEqual(slot.vmk_end_date, fields.Date.to_date("2026-10-16"))

    def test_writing_both_dates_is_taken_as_written(self):
        slot = self._slot(vmk_end_date="2026-10-11", end_hour=13.0)
        slot.write({"date": "2026-10-16", "vmk_end_date": "2026-10-17"})
        self.assertEqual(slot.vmk_end_date, fields.Date.to_date("2026-10-17"))

    def test_core_still_keeps_a_slot_inside_its_event(self):
        """Core's range check reads the computed end, so it now sees the real
        one: a weekend running past the event's end is refused."""
        with self.assertRaises(ValidationError):
            self._slot(date="2026-10-17", vmk_end_date="2026-10-19", end_hour=13.0)

    def test_a_registration_ends_when_its_slot_does(self):
        """Core reads the slot's end for the registration: nothing of ours."""
        slot = self._slot(vmk_end_date="2026-10-11", end_hour=13.0)
        registration = self.env["event.registration"].create(
            {"event_id": self.event.id, "event_slot_id": slot.id, "name": "Ada Lovelace"}
        )
        self.assertEqual(
            registration.event_end_date, fields.Datetime.to_datetime("2026-10-11 11:00:00")
        )

    def test_across_the_clock_change(self):
        """Summer time ends on 25 October 2026: 13:00 that Sunday is 12:00
        UTC, where 13:00 the day before is 11:00."""
        self.event.date_end = "2026-10-31 20:00:00"
        slot = self._slot(date="2026-10-24", vmk_end_date="2026-10-25", end_hour=13.0)
        self.assertEqual(slot.start_datetime, fields.Datetime.to_datetime("2026-10-24 16:00:00"))
        self.assertEqual(slot.end_datetime, fields.Datetime.to_datetime("2026-10-25 12:00:00"))

    def test_an_end_date_and_hour_written_together(self):
        """A one-day slot given a later end and an earlier end hour in one
        write. Odoo checks a write's plain fields before running inverses,
        so the end date is turned into the day count first; otherwise
        core's one-day hour check would refuse 18:00 to 13:00."""
        slot = self._slot()
        slot.write({"vmk_end_date": "2026-10-11", "end_hour": 13.0})
        self.assertEqual(slot.vmk_end_day_offset, 2)
        self.assertEqual(slot.end_datetime, fields.Datetime.to_datetime("2026-10-11 11:00:00"))

    def test_each_slot_counts_from_its_own_date(self):
        first, second = self._slot(), self._slot(date="2026-10-10")
        (first | second).write({"vmk_end_date": "2026-10-11"})
        self.assertEqual((first.vmk_end_day_offset, second.vmk_end_day_offset), (2, 1))

    def test_given_both_they_must_agree(self):
        """Agreeing, they are taken; disagreeing, refused rather than one
        silently winning."""
        slot = self._slot()
        slot.write({"vmk_end_date": "2026-10-11", "vmk_end_day_offset": 2, "end_hour": 13.0})
        self.assertEqual(slot.vmk_end_date, fields.Date.to_date("2026-10-11"))
        with self.assertRaisesRegex(ValidationError, "disagree"):
            slot.write({"vmk_end_date": "2026-10-16", "vmk_end_day_offset": 2})

    def test_the_form_shows_one_range(self):
        """One range in the event's timezone; core's hour row hidden, not
        removed, so other modules can still anchor on it."""
        arch = self.env["event.slot"].get_view(
            view_id=self.env.ref("event.view_event_slot_form").id
        )["arch"]
        self.assertIn('widget="vmk_event_slot_daterange"', arch)
        self.assertIn("'end_date_field': 'end_datetime'", arch)
        self.assertIn('name="start_hour"', arch)
