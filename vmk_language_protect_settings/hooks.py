# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

# The module's name until 19.0.1.1.2; see README.md.
RENAMED_FROM = "vmk_language_freeze_meta"


def protect_enabled_languages(env):
    """Protect the languages already in use when this module is installed.

    Anything customised before the module existed -- a renamed language, a
    broadened ISO code -- is already sitting in the database, and there is no way
    to tell it apart from a shipped value after the fact. Protecting every enabled
    language covers those edits without having to guess which ones were made.

    Disabled languages are left alone: they are the ~80 nobody has touched, and
    freezing them would forfeit genuine Odoo corrections for no gain. One becomes
    protected as soon as it is edited.
    """
    if env["ir.module.module"].search_count(
        [("name", "=", RENAMED_FROM), ("state", "in", ["installed", "to upgrade", "to remove"])]
    ):
        # Installed alongside the module this one was renamed from: its protections are
        # already right, including languages enabled since and never edited, which a
        # blanket protect here would wrongly freeze.
        return
    env["res.lang"].search([])._set_update_protection(True)


def restore_language_updates(env):
    """Hand the languages back to Odoo's updates when this module goes.

    Protection is the ``noupdate`` flag on ``base``'s own ``res.lang`` external ids
    (``models/res_lang.py``, ``_set_update_protection``), which nothing clears when
    the module is uninstalled: the languages would stay frozen against core
    corrections for good, with no field left to untick. So clear it on the same
    rows. Only ``base``'s ``res.lang`` records ever carry it, and no other module
    sets it there. Skipped while the module this one was renamed from is still
    installed, whose protections are still wanted.
    """
    if env["ir.module.module"].search_count(
        [("name", "=", RENAMED_FROM), ("state", "in", ["installed", "to upgrade", "to remove"])]
    ):
        return
    env["ir.model.data"].sudo().search(
        [("model", "=", "res.lang"), ("module", "=", "base"), ("noupdate", "=", True)]
    ).noupdate = False
