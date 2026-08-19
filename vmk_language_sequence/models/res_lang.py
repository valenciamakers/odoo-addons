# Copyright 2026 Valencia Makers, SL
# License AGPL-3 (https://www.gnu.org/licenses/agpl-3.0.html).

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
        # `res.lang` declares `active` with no default, so a language created
        # without one is disabled and belongs in the disabled block. `create()`
        # re-parks it at the end of that block straight away, making this default
        # visible only if that ever fails -- in which case landing at the head of
        # the disabled languages beats wedging in among the enabled ones.
        default=DISABLED_SEQUENCE_BASE,
        help="Order in which enabled languages are offered, lowest first: in the "
        "website language selector, and in the language dropdowns of users "
        "and contacts.",
    )

    @property
    def CACHED_FIELDS(self) -> OrderedSet:
        # Carrying ``sequence`` in the cached language data lets the ordering
        # overrides below sort without a query of their own.
        return OrderedSet([*super().CACHED_FIELDS, "sequence"])

    def _sorted_by_sequence(
        self, langs: LangDataDict, sequences: dict | None = None
    ) -> LangDataDict:
        """Re-order a LangDataDict by ``sequence``, falling back to name.

        ``sequences`` supplies values read from somewhere fresher than ``langs``,
        for callers whose data comes from a cache this module does not invalidate.
        """

        def sort_key(item):
            code, data = item
            sequence = data.sequence if sequences is None else sequences.get(code, data.sequence)
            return (sequence, data.name)

        return LangDataDict(dict(sorted(langs.items(), key=sort_key)))

    def _live_sequences(self) -> dict:
        """Map language code to its current sequence.

        Built as a plain dict on purpose: ``LangDataDict`` returns a dummy entry
        for unknown keys instead of raising, so ``in`` and ``.get()`` on it are
        always truthy and cannot be used to tell a missing language apart.
        """
        return {
            code: data.sequence
            for code, data in self._get_active_by("code").items()
        }

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
        #
        # The sequences are read from ``_get_active_by`` rather than from the data
        # ``super()`` returns. That cache lives on 'default', which nothing
        # invalidates when a sequence changes, so trusting its values would mean
        # clearing the whole default cache -- every compiled template and view
        # lookup on the site -- on each reorder. ``_get_active_by`` is on 'stable',
        # which core's own ``res.lang.write()`` already clears.
        return self._sorted_by_sequence(super()._get_frontend(), self._live_sequences())

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
        # No cache clearing of our own: ``super().write()`` clears 'stable', and
        # ``_get_frontend`` deliberately reads its sequences from there.
        return res
