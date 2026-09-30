# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import api, fields, models
from odoo.addons.base.models.res_lang import LangData, LangDataDict

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
    def _cached_data_fields(self) -> tuple:
        # ``res.lang`` is a ``CachedModel``: it keeps these fields of the active
        # languages on the 'stable' cache, and clears that cache when a write
        # touches one of them (``_clear_cache_on_fields`` is derived from this).
        # Adding ``sequence`` does two things at once: the ordering below sorts
        # without a query of its own, and dragging a language invalidates
        # exactly the language data and nothing wider. A property rather than a
        # literal tuple so that a field core adds later is not silently dropped.
        return (*super()._cached_data_fields, "sequence")

    @api.model
    def _get_active_langs(self):
        # Core's version is ``get_all()``, the cached records in id order. Every
        # list of languages core builds from the cache starts here:
        # ``_get_active_by()`` (so ``_get_data()``, and ``http_routing``'s
        # frontend selector) and ``get_installed()`` below. Sorting here puts
        # them all in our order, and ``_get_active_by()`` stays cached by core.
        #
        # Consumers that sort ``_get_active_langs()`` themselves, by name, are
        # out of reach and stay alphabetical; see the README.
        return super()._get_active_langs().sorted(lambda lang: (lang.sequence, lang.name))

    @api.model
    @api.readonly
    def get_installed(self) -> list[tuple[str, str]]:
        """Return installed languages' (code, name) pairs, in our order.

        Core sorts by name after asking ``_get_active_langs()``, so the order
        above would not reach this, the source of every language dropdown.
        """
        return [(lang.code, lang.name) for lang in self.sudo()._get_active_langs()]

    def _get_frontend(self) -> LangDataDict:
        # ``website`` builds the site language selector from
        # ``language_ids.sorted('name')``, bypassing ``_get_active_langs`` again.
        # No cache of our own here: ``super()`` is already cached, and this runs
        # once per page render over a handful of entries.
        #
        # The order is taken from ``_get_active_by('code')`` rather than from
        # the ``sequence`` inside the data ``super()`` returns. That cache lives
        # on 'default', which nothing invalidates when a sequence changes, so
        # trusting its values would mean clearing the whole default cache --
        # every compiled template and view lookup on the site -- on each reorder.
        # ``_get_active_by`` is on 'stable', which ``write()`` of a cached field
        # already clears.
        langs = super()._get_frontend()
        position = {code: index for index, code in enumerate(self._get_active_by("code"))}
        # A plain dict: ``LangDataDict`` answers every key, with a dummy entry
        # for a missing one, so ``.get()`` on it cannot say a language is absent.
        last = len(position)
        ordered = LangDataDict(
            dict(sorted(langs.items(), key=lambda item: position.get(item[0], last)))
        )
        return self._hreflang_in_order(ordered)

    @staticmethod
    def _hreflang_in_order(langs: LangDataDict) -> LangDataDict:
        """Re-assign ``website``'s hreflang codes in the order of ``langs``.

        ``website``'s ``_get_frontend()`` gives each base language's short code
        (``en``) to the first variant it meets in *name* order and region-qualifies
        the rest (``en-us``), so re-sorting afterwards would leave English (UK)
        generic wherever it sits. This is core's own loop, walked in our order,
        keeping its exception that Latin American Spanish, when enabled, is the
        generic ``es``. Outside a website request there are no hreflang codes and
        the data passes through untouched.
        """
        if not any("hreflang" in data for data in langs.values()):
            return langs
        es_419_exists = "es_419" in langs
        shortened = set()
        result = {}
        for code, data in langs.items():
            short_code = code.split("_")[0]
            if short_code not in shortened and not (
                short_code == "es" and code != "es_419" and es_419_exists
            ):
                hreflang = short_code
                shortened.add(short_code)
            else:
                hreflang = code.lower().replace("_", "-")
            result[code] = LangData(dict(data, hreflang=hreflang))
        return LangDataDict(result)

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
        # No cache clearing of our own: ``sequence`` is one of ``_cached_data_fields``,
        # so ``super().write()`` clears 'stable', and ``_get_frontend`` deliberately
        # reads its order from there.
        return res
