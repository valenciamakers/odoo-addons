# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).


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
    env["res.lang"].search([])._set_update_protection(True)


def restore_language_updates(env):
    """Hand the languages back to Odoo's updates when this module goes.

    Protection is the ``noupdate`` flag on ``base``'s own ``res.lang`` external ids
    (``models/res_lang.py``, ``_set_update_protection``), which nothing clears when
    the module is uninstalled: the languages would stay frozen against core
    corrections for good, with no field left to untick. So clear it on the same
    rows. Only ``base``'s ``res.lang`` records ever carry it, and no other module
    sets it there. (On 19 this stands aside for the module this one was renamed
    from; that module never existed on 18, so there is nothing to wait for.)
    """
    env["ir.model.data"].sudo().search(
        [("model", "=", "res.lang"), ("module", "=", "base"), ("noupdate", "=", True)]
    ).noupdate = False
