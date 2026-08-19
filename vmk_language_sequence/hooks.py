# Copyright 2026 Valencia Makers, SL
# License AGPL-3 (https://www.gnu.org/licenses/agpl-3.0.html).

from .models.res_lang import DISABLED_SEQUENCE_BASE


def seed_language_sequence(env):
    """Give every language a distinct sequence, enabled ones first.

    Two problems are solved at once. The Languages action opens with
    ``active_test: False``, and a list view carrying a handle field is ordered
    ``sequence, id`` by the web client rather than by ``_order`` -- so leaving
    every language on the same default would interleave the enabled ones with the
    80-odd disabled ones by database id. Seeding a low block for the enabled
    languages and a high one for the rest reproduces the grouping the list had
    before this module added the handle.

    Distinct values matter just as much: Odoo only rewrites the records between
    the two positions of a drag when the sequences it sees are strictly
    increasing. On tied values it resequences the whole list instead, which would
    scatter the enabled languages through the disabled block on the first drag.
    """
    langs = (
        env["res.lang"]
        .with_context(active_test=False)
        .search([], order="active desc, name")
    )
    enabled = langs.filtered("active")
    for index, lang in enumerate(enabled, start=1):
        lang.sequence = index * 10
    for index, lang in enumerate(langs - enabled, start=1):
        lang.sequence = DISABLED_SEQUENCE_BASE + index * 10
