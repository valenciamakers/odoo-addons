# Copyright 2026 Valencia Makers, SL
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models, tools
from odoo.addons.base.models.res_lang import LangDataDict
from odoo.tools import OrderedSet

# Disabled languages are parked above this, keeping the enabled ones -- the only
# ones this module exists to order -- together at the top of the Languages list.
DISABLED_SEQUENCE_BASE = 10000


class ResLang(models.Model):
    _inherit = "res.lang"
    # ``active desc`` is kept ahead of ``sequence`` so a plain ``search()``
    # anywhere in Odoo still returns enabled languages first as it does in stock
    # (``active desc, name``); ``sequence`` only replaces ``name`` as the tiebreak.
    # Note this does not order the Languages list itself: a list view carrying a
    # handle field and no ``default_order`` gets ``<handle field>, id`` imposed by
    # the web client (see ``list_arch_parser.js``), which is what keeps dragging
    # WYSIWYG there.
    _order = "active desc, sequence, name"

    sequence = fields.Integer(
        default=10,
        help="Order in which enabled languages are offered, lowest first: in the "
        "website language selector, and in the language dropdowns of users "
        "and contacts.",
    )

    @property
    def CACHED_FIELDS(self) -> OrderedSet:
        # Carrying ``sequence`` in the cached language data lets the ordering
        # overrides below sort without a query of their own.
        return OrderedSet([*super().CACHED_FIELDS, "sequence"])

    def _sorted_by_sequence(self, langs: LangDataDict) -> LangDataDict:
        """Re-order a LangDataDict by ``sequence``, falling back to name."""
        return LangDataDict(
            dict(
                sorted(
                    langs.items(),
                    key=lambda item: (item[1].sequence, item[1].name),
                )
            )
        )

    @tools.ormcache("field", cache="stable")
    def _get_active_by(self, field: str) -> LangDataDict:
        # Core builds this with ``search_fetch(..., order='name')``, a hardcoded
        # order that ``_order`` cannot influence. It is the single chokepoint
        # behind both ``get_installed()`` (the language dropdowns on users and
        # contacts) and ``http_routing``'s frontend selector, so re-sorting here
        # covers both at once.
        #
        # Cached in turn because ``_get_data`` reaches this on every date and
        # number format, far too often to re-sort each time.
        return self._sorted_by_sequence(super()._get_active_by(field))

    def _get_frontend(self) -> LangDataDict:
        # ``website`` builds the site language selector from
        # ``language_ids.sorted('name')``, bypassing ``_order`` again. No cache of
        # our own here: ``super()`` is already cached, and this runs once per page
        # render over a handful of entries.
        return self._sorted_by_sequence(super()._get_frontend())

    def _park_in_active_block(self):
        """Move these languages to the end of the block matching their state.

        Enabling a language would otherwise leave it on whatever sequence it was
        seeded with, stranding it among the disabled ones instead of joining the
        enabled group it now belongs to. Disabling one strands it the other way
        around.
        """
        Lang = self.env["res.lang"].with_context(active_test=False)
        enabled = self.filtered("active")
        for is_active, langs in ((True, enabled), (False, self - enabled)):
            if not langs:
                continue
            peers = Lang.search(
                [("active", "=", is_active), ("id", "not in", langs.ids)]
            )
            floor = 0 if is_active else DISABLED_SEQUENCE_BASE
            start = max([*peers.mapped("sequence"), floor])
            for index, lang in enumerate(langs, start=1):
                lang.sequence = start + index * 10

    @api.model_create_multi
    def create(self, vals_list):
        langs = super().create(vals_list)
        # A language added by hand -- one Odoo does not ship -- would otherwise
        # keep the field default and land in the middle of the seeded blocks,
        # tying with whatever sits on 10 and costing the strictly increasing
        # sequences that keep a drag local.
        unplaced = self.browse()
        for lang, vals in zip(langs, vals_list):
            if "sequence" not in vals:
                unplaced |= lang
        if unplaced:
            unplaced._park_in_active_block()
        return langs

    def write(self, vals):
        changing_state = (
            self.filtered(lambda lang: lang.active != vals["active"])
            if "active" in vals
            else self.browse()
        )
        res = super().write(vals)
        if changing_state:
            changing_state._park_in_active_block()
        if "sequence" in vals:
            # ``super().write()`` clears only the 'stable' cache, while
            # ``website._get_frontend`` is cached on the default one -- without
            # this the site selector keeps serving the previous order.
            self.env.registry.clear_cache()
        return res
