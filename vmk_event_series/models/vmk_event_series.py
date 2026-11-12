# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import html_translate


class VmkEventSeries(models.Model):
    """An event run again and again, such as a monthly workshop. Each date is
    an ordinary event, linked by its series_id; the series holds what every
    date shares, for its page on the website (vmk_website_event_series)."""

    _name = "vmk.event.series"
    _description = "Event Series"
    _order = "sequence, name, id"

    name = fields.Char(required=True, translate=True)
    subtitle = fields.Char(translate=True)
    description = fields.Html(
        translate=html_translate, sanitize_attributes=False, sanitize_form=False
    )
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company,
        index="btree_not_null",
    )
    event_type_id = fields.Many2one(
        "event.type",
        string="Template",
        help="The template a new date starts from: its tickets, communications, and the rest.",
    )
    event_ids = fields.One2many("event.event", "series_id", string="Events")
    event_count = fields.Integer(string="Event Count", compute="_compute_event_counts")
    upcoming_event_count = fields.Integer(
        string="Upcoming Events", compute="_compute_event_counts"
    )
    next_event_id = fields.Many2one(
        "event.event", string="Next Event", compute="_compute_next_event_id"
    )

    @api.model
    def _upcoming_domain(self):
        """Current and upcoming: not yet ended, as core's Upcoming/Running
        filter has it."""
        return [("date_end", ">=", fields.Datetime.now())]

    @api.depends("event_ids", "event_ids.date_end")
    def _compute_event_counts(self):
        Event = self.env["event.event"]
        totals = dict(Event._read_group(
            [("series_id", "in", self.ids)], ["series_id"], ["__count"]
        ))
        upcoming = dict(Event._read_group(
            [("series_id", "in", self.ids), *self._upcoming_domain()],
            ["series_id"], ["__count"],
        ))
        for series in self:
            series.event_count = totals.get(series, 0)
            series.upcoming_event_count = upcoming.get(series, 0)

    @api.depends("event_ids", "event_ids.date_begin", "event_ids.date_end")
    def _compute_next_event_id(self):
        for series in self:
            series.next_event_id = self.env["event.event"].search(
                [("series_id", "=", series.id), *self._upcoming_domain()],
                order="date_begin, id", limit=1,
            ) if series.id else False

    @api.ondelete(at_uninstall=False)
    def _unlink_except_with_events(self):
        """Say why, where the database's own refusal (series_id is
        ondelete='restrict') would only name the constraint."""
        events = self.env["event.event"].with_context(active_test=False).search_count(
            [("series_id", "in", self.ids)], limit=1
        )
        if events:
            raise UserError(self.env._(
                "A series with events cannot be deleted. Archive it instead, or move its "
                "events to another series first."
            ))

    def action_view_events(self):
        """The series' events, every view of them, a new one in the series."""
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id("event.action_event_view")
        action.update({
            "domain": [("series_id", "=", self.id)],
            "context": {
                "default_series_id": self.id,
                "default_event_type_id": self.event_type_id.id,
                "default_name": self.name,
            },
        })
        return action

    def action_new_date(self):
        """A new event in the series, from its template and with its name."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("New Date"),
            "res_model": "event.event",
            "view_mode": "form",
            "views": [(False, "form")],
            "target": "current",
            "context": {
                "default_series_id": self.id,
                "default_event_type_id": self.event_type_id.id,
                "default_name": self.name,
                "default_company_id": self.company_id.id or self.env.company.id,
            },
        }
