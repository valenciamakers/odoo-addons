# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import http
from odoo.addons.web.controllers.webclient import ModelTranslations
from odoo.http import request


class ModelTranslationsInSequence(ModelTranslations):
    @http.route()
    def get_translation_for_field(self, *args, **kwargs):
        """Hand the translation dialog its languages in our order.

        Core builds the payload from ``_get_active_langs().sorted('name')``, in
        the route itself, so the order of ``_get_active_langs()`` never reaches
        it. The dialog draws the languages in the order of the ``languages``
        object, sorting nothing itself (``translation_components.xml``), so
        putting that object in our order is the whole fix, with no JavaScript.

        ``terms`` is sorted as well. Core builds it from a ``set`` of language
        codes, so its order is arbitrary, and the dialog opens a rich-text field
        on the first language in it that is not the user's own
        (``_selfUpdate`` in ``translation_model.js``).

        The result is re-ordered rather than rebuilt, so nothing of core's is
        copied here; a key core stops sending is left alone.
        """
        result = super().get_translation_for_field(*args, **kwargs)
        position = {
            lang.code: index
            for index, lang in enumerate(request.env["res.lang"].sudo()._get_active_langs())
        }
        last = len(position)
        languages = result.get("languages")
        if isinstance(languages, dict):
            result["languages"] = dict(
                sorted(languages.items(), key=lambda item: position.get(item[0], last))
            )
        terms = result.get("terms")
        if isinstance(terms, list):
            result["terms"] = sorted(
                terms, key=lambda term: position.get(term.get("lang"), last)
            )
        return result
