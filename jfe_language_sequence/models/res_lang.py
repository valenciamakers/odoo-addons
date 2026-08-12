# Copyright 2026 Valencia Makers, SL
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models, tools
from odoo.addons.base.models.res_lang import LangDataDict
from odoo.tools import OrderedSet


class ResLang(models.Model):
    _inherit = "res.lang"
    # ``active desc`` is deliberately kept ahead of ``sequence``. The Languages
    # action opens with ``active_test: False``, so the list shows every language
    # Odoo ships, not just the enabled ones; keeping the enabled ones grouped on
    # top preserves the stock list and means a newly activated language surfaces
    # into that group rather than staying buried among the disabled ones. Every
    # consumer of the ordering below sees only active languages, so the prefix is
    # inert for them.
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

    def write(self, vals):
        res = super().write(vals)
        if "sequence" in vals:
            # ``super().write()`` clears only the 'stable' cache, while
            # ``website._get_frontend`` is cached on the default one -- without
            # this the site selector keeps serving the previous order.
            self.env.registry.clear_cache()
        return res
