# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).
"""Stop apps that copy a record's email onto its contact from overwriting the primary.

CRM, Recruitment, and Helpdesk each keep a record's email and its contact's email in
step: when they differ, the record's is written onto the contact. In core they only
differ when someone edits one of them, because core matches mail on the primary
address alone. This module also matches on additional addresses, so a lead created
from one arrives with an email that differs from its contact's primary -- and the sync
then overwrites the primary with it, losing the old one.

None of those apps is a dependency, so the fix cannot be an ``_inherit``. Instead
``res.partner._register_hook`` calls :func:`install`, which patches the sync of each
app that is present onto its registry class, as ``base_automation`` patches models
(``base_automation/models/base_automation.py``, ``_register_hook``). Every registry
load builds fresh classes and calls the hook again, so an app installed later is
covered, and nothing needs undoing on uninstall.

A patched method that Odoo renames would stop applying without raising, so a missing
method is logged as a warning, and the tests assert each patch is in place.
"""

import logging

from odoo.tools import email_normalize

_logger = logging.getLogger(__name__)

# Marks a method as ours, so a second call on the same registry does not wrap it twice.
PATCHED = "_vmk_keeps_primary_email"

# Set around a sync that has no decision method to patch; res.partner.write honours it.
KEEP_PRIMARY = "vmk_keep_primary_email"


def is_additional(partner, email):
    """Whether ``email`` is one of ``partner``'s own additional addresses."""
    normalized = email_normalize(email or "")
    return bool(normalized) and normalized in partner.vmk_email_ids.mapped("email_normalized")


def _no_update_for_additional(email_field):
    """Wrap ``_get_partner_email_update``: an additional address is no reason to update.

    CRM and Helpdesk decide the sync here, and the same answer drives the form's
    warning that the contact's email will be updated, so both stop together.
    """

    def _get_partner_email_update(self, *args, **kwargs):
        if is_additional(self.partner_id, self[email_field]):
            return False
        return _get_partner_email_update.origin(self, *args, **kwargs)

    return _get_partner_email_update


def _keep_primary():
    """Wrap an inverse that writes the contact's email inline, with no decision method.

    Recruitment's ``_inverse_partner_email`` syncs name, email, and phone in one loop.
    Run under :data:`KEEP_PRIMARY`, ``res.partner.write`` drops only the email, and
    only when it is one of that contact's additional addresses.
    """

    def _inverse_partner_email(self, *args, **kwargs):
        return _inverse_partner_email.origin(
            self.with_context(**{KEEP_PRIMARY: True}), *args, **kwargs
        )

    return _inverse_partner_email


# model -> method -> factory. The field is where the record keeps its email.
PATCHES = {
    "crm.lead": {"_get_partner_email_update": lambda: _no_update_for_additional("email_from")},
    "helpdesk.ticket": {
        "_get_partner_email_update": lambda: _no_update_for_additional("partner_email")
    },
    "hr.applicant": {"_inverse_partner_email": _keep_primary},
}


def install(env):
    """Patch the email sync of every app in :data:`PATCHES` that this registry has."""
    for model_name, methods in PATCHES.items():
        model_class = env.registry.get(model_name)
        if model_class is None:
            continue
        for name, factory in methods.items():
            current = getattr(model_class, name, None)
            if current is None:
                _logger.warning(
                    "%s.%s is gone, so an email from a contact's additional address may "
                    "overwrite its primary address. Re-check vmk_partner_email_multiple's "
                    "patches against this version of Odoo.",
                    model_name,
                    name,
                )
                continue
            if getattr(current, PATCHED, False):
                continue
            method = factory()
            method.origin = current
            setattr(method, PATCHED, True)
            setattr(model_class, name, method)
