# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from datetime import timedelta

from odoo import fields
from odoo.exceptions import AccessError, UserError
from odoo.tests.common import TransactionCase, new_test_user, tagged


@tagged("post_install", "-at_install")
class TestSeries(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.template = cls.env["event.type"].create({"name": "Evening workshop"})
        cls.series = cls.env["vmk.event.series"].create({
            "name": "Intro to 3D Printing",
            "event_type_id": cls.template.id,
        })
        now = fields.Datetime.now()

        def event(name, days):
            return {
                "name": name,
                "series_id": cls.series.id,
                "date_begin": now + timedelta(days=days),
                "date_end": now + timedelta(days=days, hours=2),
            }

        cls.past, cls.soon, cls.later = cls.env["event.event"].create([
            event("Past date", -30), event("Next date", 3), event("Later date", 33),
        ])

    def test_counts_and_next_event(self):
        self.assertEqual(self.series.event_count, 3)
        self.assertEqual(self.series.upcoming_event_count, 2)
        self.assertEqual(self.series.next_event_id, self.soon)

    def test_a_running_event_is_current(self):
        """An event that has started but not ended is still listed: the
        series shows current and upcoming dates."""
        self.soon.write({
            "date_begin": fields.Datetime.now() - timedelta(hours=1),
            "date_end": fields.Datetime.now() + timedelta(hours=1),
        })
        self.series.invalidate_recordset(["upcoming_event_count", "next_event_id"])
        self.assertEqual(self.series.upcoming_event_count, 2)
        self.assertEqual(self.series.next_event_id, self.soon)

    def test_a_series_fills_nothing_in(self):
        """Unlike a template, choosing a series is a plain link."""
        self.assertFalse(self.soon.event_type_id)
        self.assertEqual(self.soon.name, "Next date")

    def test_new_date_starts_from_the_series(self):
        action = self.series.action_new_date()
        self.assertEqual(action["res_model"], "event.event")
        context = action["context"]
        self.assertEqual(context["default_series_id"], self.series.id)
        self.assertEqual(context["default_event_type_id"], self.template.id)
        self.assertEqual(context["default_name"], "Intro to 3D Printing")
        # The template's defaults reach the new event, as from any template.
        new = self.env["event.event"].with_context(context).create({
            "date_begin": fields.Datetime.now() + timedelta(days=60),
            "date_end": fields.Datetime.now() + timedelta(days=60, hours=2),
        })
        self.assertEqual(new.series_id, self.series)
        self.assertEqual(new.event_type_id, self.template)
        self.assertEqual(new.name, "Intro to 3D Printing")

    def test_events_of_the_series(self):
        action = self.series.action_view_events()
        self.assertEqual(self.env["event.event"].search(action["domain"]),
                         self.past + self.soon + self.later)
        self.assertEqual(action["context"]["default_series_id"], self.series.id)

    def test_a_series_with_events_cannot_be_deleted(self):
        with self.assertRaises(UserError):
            self.series.unlink()
        # Archived events count too: they still point at the series.
        self.series.event_ids.action_archive()
        with self.assertRaises(UserError):
            self.series.unlink()

    def test_a_series_without_events_can_be_deleted(self):
        empty = self.env["vmk.event.series"].create({"name": "Never run"})
        empty.unlink()
        self.assertFalse(empty.exists())

    def test_access(self):
        desk = new_test_user(self.env, "vmk_series_desk", groups="event.group_event_registration_desk")
        user = new_test_user(self.env, "vmk_series_user", groups="event.group_event_user")
        manager = new_test_user(self.env, "vmk_series_manager", groups="event.group_event_manager")
        self.series.with_user(desk).check_access("read")
        with self.assertRaises(AccessError):
            self.series.with_user(desk).check_access("write")
        self.series.with_user(user).check_access("write")
        with self.assertRaises(AccessError):
            self.series.with_user(user).check_access("unlink")
        self.series.with_user(manager).check_access("unlink")
        other = self.env["res.company"].create({"name": "Other company"})
        foreign = self.env["vmk.event.series"].create({"name": "Elsewhere", "company_id": other.id})
        with self.assertRaises(AccessError):
            foreign.with_user(manager).check_access("read")
