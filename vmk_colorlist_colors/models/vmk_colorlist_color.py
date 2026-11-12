# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

import re

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import code_translations

from . import palette

HEX_COLOR = re.compile(r"#[0-9a-f]{6}")

# Where the generated stylesheets live, as attachments. The first part of the
# path is not an addon, so ir.asset reads it as an attachment's URL, as it
# does website's own customized stylesheets (/_custom/...).
LIGHT_URL = "/_custom/vmk_colorlist_colors/colors.scss"
DARK_URL = "/_custom/vmk_colorlist_colors/colors.dark.scss"


class VmkColorlistColor(models.Model):
    """One of the twelve colors Odoo offers wherever a record has a color:
    tags, kanban cards, calendars. A record stores only what was changed;
    empty, a field means Odoo's own color or name.

    The records are made by data/vmk_colorlist_color_data.xml, one per slot,
    and are never created or deleted otherwise.
    """

    _name = "vmk.colorlist.color"
    _description = "Color"
    _order = "slot"

    slot = fields.Integer(required=True, readonly=True)
    custom_color = fields.Char(string="Custom Color")
    color = fields.Char(
        compute="_compute_color",
        inverse="_inverse_color",
        help="Choosing Odoo's own color again removes the custom one.",
    )
    name = fields.Char(
        translate=True,
        help="Empty, the color keeps Odoo's name, translated as Odoo translates it.",
    )
    odoo_color = fields.Char(string="Default Color", compute="_compute_odoo")
    odoo_name = fields.Char(string="Default Name", compute="_compute_odoo")
    is_custom = fields.Boolean(compute="_compute_is_custom")

    _slot_unique = models.Constraint("unique(slot)", "Each color appears once.")

    @api.depends("slot")
    @api.depends_context("lang")
    def _compute_odoo(self):
        names = self._odoo_names()
        for record in self:
            record.odoo_color = palette.COLORS[record.slot]
            record.odoo_name = names[record.slot]

    @api.depends("custom_color", "slot")
    def _compute_color(self):
        for record in self:
            record.color = record.custom_color or palette.COLORS[record.slot]

    def _inverse_color(self):
        for record in self:
            color = (record.color or "").lower() or False
            record.custom_color = False if color == palette.COLORS[record.slot] else color

    @api.depends("custom_color", "name")
    def _compute_is_custom(self):
        for record in self:
            record.is_custom = bool(record.custom_color or record.name)

    @api.depends("name", "slot")
    @api.depends_context("lang")
    def _compute_display_name(self):
        names = self._odoo_names()
        for record in self:
            record.display_name = record.name or names[record.slot]

    @api.constrains("custom_color")
    def _check_custom_color(self):
        for record in self:
            if record.custom_color and not HEX_COLOR.fullmatch(record.custom_color):
                raise ValidationError(self.env._(
                    "Choose a color with the color picker. %(value)s is not a color in the "
                    "form #rrggbb.",
                    value=record.custom_color,
                ))

    @api.constrains("name", "slot")
    def _check_no_color_name(self):
        for record in self:
            if record.slot == 0 and record.name:
                raise ValidationError(self.env._(
                    "No color keeps its name: Odoo gives it a meaning of its own, such as "
                    "hiding an event tag from the website."
                ))

    def _odoo_names(self):
        """Odoo's names for the twelve colors, in the current language.

        They are JavaScript terms of `web` (colorlist.js), so their
        translations are web's JavaScript translations, which Python's `_()`
        does not reach.
        """
        lang = self.env.lang or "en_US"
        if lang == "en_US":
            return palette.NAMES
        messages = code_translations.get_web_translations("web", lang)["messages"]
        translated = {message["id"]: message["string"] for message in messages}
        return tuple(translated.get(name, name) for name in palette.NAMES)

    def action_reset(self):
        """Back to Odoo's color and name. The page reloads, so the new colors
        show everywhere at once."""
        self.write({"custom_color": False, "name": False})
        return {"type": "ir.actions.client", "tag": "reload"}

    def action_reset_all(self):
        return self.search([]).action_reset()

    def write(self, vals):
        result = super().write(vals)
        # A new color arrives as custom_color, written by color's inverse.
        if "custom_color" in vals:
            self._update_stylesheets()
        return result

    # The stylesheets

    @api.model
    def _update_stylesheets(self):
        """Write the stylesheets setting Odoo's color variables, and put them
        in the asset bundles, or remove both when no color is custom.

        The light one goes first in web._assets_primary_variables, ahead of
        web's primary_variables.scss, whose values are all !default, so ours
        win in the backend and on every website. Enterprise's dark mode sets
        its own; the dark one goes just before the light one in its bundle
        (web.dark_mode_variables, which only Enterprise has).
        """
        records = self.sudo().search([])
        Attachment = self.env["ir.attachment"].sudo()
        Asset = self.env["ir.asset"].sudo()
        attachments = Attachment.search([("url", "in", [LIGHT_URL, DARK_URL])])
        assets = Asset.search([("path", "in", [LIGHT_URL, DARK_URL])])
        if not any(records.mapped("custom_color")):
            assets.unlink()
            attachments.unlink()
            return

        colors = list(palette.COLORS)
        dark_colors = list(palette.DARK_COLORS)
        light = {
            "border": list(palette.BORDER),
            "bg_subtle": list(palette.BG_SUBTLE),
            "text_emphasis": list(palette.TEXT_EMPHASIS),
        }
        dark = {
            "border": list(palette.DARK_BORDER),
            "bg_subtle": list(palette.DARK_BG_SUBTLE),
            "text_emphasis": list(palette.DARK_TEXT_EMPHASIS),
        }
        for record in records.filtered("custom_color"):
            slot, color = record.slot, record.custom_color
            colors[slot] = dark_colors[slot] = color
            for role, shade in palette.shades(color).items():
                light[role][slot] = shade
            for role, shade in palette.shades(color, dark=True).items():
                dark[role][slot] = shade

        def scss_list(values):
            return ", ".join(values)

        header = (
            "// Written by vmk_colorlist_colors from Settings > Colors. Changes made\n"
            "// here are lost the next time a color is saved.\n"
        )
        # !default, so that in Enterprise's dark mode, where the dark
        # stylesheet comes first, its values stand.
        light_scss = header + "".join(
            f"$o-colors{suffix}: {scss_list(values)} !default;\n"
            for suffix, values in (
                ("", colors),
                ("-border", light["border"]),
                ("-bg-subtle", light["bg_subtle"]),
                ("-text-emphasis", light["text_emphasis"]),
            )
        )
        # Enterprise darkens $o-colors-original into $o-colors by appending
        # to it, so $o-colors is set here to an empty list: the light
        # stylesheet's !default then leaves it alone, and so does
        # Enterprise's own.
        dark_scss = header + "$o-colors: ();\n" + "".join(
            f"$o-colors{suffix}: {scss_list(values)};\n"
            for suffix, values in (
                ("-original", dark_colors),
                ("-border", dark["border"]),
                ("-bg-subtle", dark["bg_subtle"]),
                ("-text-emphasis", dark["text_emphasis"]),
            )
        )

        for url, scss in ((LIGHT_URL, light_scss), (DARK_URL, dark_scss)):
            raw = scss.encode()
            attachment = attachments.filtered(lambda a, url=url: a.url == url)
            if attachment:
                if attachment.raw != raw:
                    attachment.raw = raw
                    # The bundles are cached by their list of files, which
                    # has not changed, so the cache has to be told, as
                    # website does when it saves a customized stylesheet.
                    self.env.transaction.invalidate_ormcache("assets")
            else:
                Attachment.create({
                    "name": url.rsplit("/", 1)[-1],
                    "type": "binary",
                    "mimetype": "text/scss",
                    "raw": raw,
                    "url": url,
                })
        if not assets.filtered(lambda a: a.path == LIGHT_URL):
            Asset.create({
                "name": "Colors: Odoo's color variables",
                "bundle": "web._assets_primary_variables",
                "directive": "prepend",
                "path": LIGHT_URL,
            })
        if not assets.filtered(lambda a: a.path == DARK_URL):
            Asset.create({
                "name": "Colors: Odoo's color variables, dark mode",
                "bundle": "web.dark_mode_variables",
                "directive": "before",
                "target": LIGHT_URL,
                "path": DARK_URL,
            })
