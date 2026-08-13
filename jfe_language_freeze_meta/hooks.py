# Copyright 2026 Valencia Makers, SL
# License MIT (https://opensource.org/licenses/MIT).


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
