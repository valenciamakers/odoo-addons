# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).
"""Demo data for the Apps Store screenshots, described in ../README.md.

Idempotent: every record is found by name before it is created, so running this twice leaves the
same state as running it once. Works on both Odoo 18 and 19 -- the two differ in one place, event
slots, handled below by branching on ``odoo.release.series``.

    cd "Odoo Addons - Custom (18.0)"                     # or the 19.0 checkout
    SERIES=18.0 DB=shots ../../Tech\\ Stack/odoo-dev/odev shell < tools/shots/demo/seed.py

Odoo 18 has no ``event.slot`` model and no demo contacts (``without_demo = all`` in both series'
harness config), so this script creates Marc Demo and Edith Sanchez itself, with the same avatars
Odoo's own demo data uses (``base/static/img/user_demo-image.png`` and
``base/static/img/res_partner_address_14.jpg``), and Beginner's Bootcamp becomes one ordinary event
(a Friday evening to Sunday afternoon) rather than a multi-slot one.

``open_studio_evening(env)`` is deliberately not called by this script: it makes a published event
starting "in an hour", which only means something run right before a capture. Call it on its own,
right before capturing vmk_event_registration_deadline's public page:

    (cat tools/shots/demo/seed.py; echo "open_studio_evening(env)") | SERIES=18.0 DB=shots ../../Tech\\ Stack/odoo-dev/odev shell
"""
import base64
from datetime import datetime, timedelta

import odoo.tools as tools

IS_18 = odoo.release.series == "18.0"

print(f"seeding demo data for Odoo {odoo.release.series} ...")


# ---------------------------------------------------------------------------
# Company: Valencia Makers, in Spain. Organizer and Venue both default to the
# company's own partner, so renaming it once gets both right on every event.
# ---------------------------------------------------------------------------
company = env.company
if company.name != "Valencia Makers":
    company.write({"name": "Valencia Makers"})
if company.partner_id.name != "Valencia Makers":
    company.partner_id.write({"name": "Valencia Makers"})
spain = env.ref("base.es")
if company.country_id != spain:
    company.write({"country_id": spain.id})

admin = env.ref("base.user_admin")
if admin.name != "Mitchell Admin" or admin.lang != "en_GB":
    admin.write({"name": "Mitchell Admin", "lang": "en_GB"})
# A user's letter avatar is generated once, from the name it was created with, so a database whose
# admin started as "Administrator" shows an A. Regenerate it only while it is still a generated one.
if base64.b64decode(admin.image_1920 or b"").startswith(b"<?xml") and b">M</text>" not in base64.b64decode(admin.image_1920):
    admin.image_1920 = admin.partner_id._avatar_generate_svg()


# ---------------------------------------------------------------------------
# Languages: six active, all on the website, English (UK) as its default.
# ---------------------------------------------------------------------------
LANG_CODES = ["en_GB", "en_US", "ca_ES", "fr_FR", "de_DE", "es_ES"]
Lang = env["res.lang"].with_context(active_test=False)
for code in LANG_CODES:
    lang = Lang.search([("code", "=", code)], limit=1)
    if not lang or not lang.active:
        Lang._activate_and_install_lang(code)

langs = env["res.lang"].search([("code", "in", LANG_CODES)])
website = env["website"].search([], limit=1)
en_gb = env["res.lang"].search([("code", "=", "en_GB")], limit=1)
website.write({"language_ids": [(6, 0, langs.ids)], "default_lang_id": en_gb.id})


# ---------------------------------------------------------------------------
# Marc Demo and Edith Sanchez: find or create, with core's own demo avatars.
# ---------------------------------------------------------------------------
Partner = env["res.partner"]


def avatar(path):
    with tools.file_open(path, mode="rb") as f:
        return base64.b64encode(f.read())


def find_or_create_partner(name, **vals):
    partner = Partner.search([("name", "=", name)], limit=1)
    if not partner:
        partner = Partner.create({"name": name, **vals})
    return partner


marc = find_or_create_partner("Marc Demo", image_1920=avatar("base/static/img/user_demo-image.png"))
edith = find_or_create_partner(
    "Edith Sanchez", image_1920=avatar("base/static/img/res_partner_address_14.jpg")
)


# ---------------------------------------------------------------------------
# Events, with hosts. Beginner's Bootcamp has no slots on 18 -- see the
# module docstring in vmk_event_registration_deadline/models/event_event.py.
# ---------------------------------------------------------------------------
Event = env["event.event"]
Host = env["vmk.event.host"]
madrid = "Europe/Madrid"


def find_or_create_event(name, **vals):
    # Responsible: the admin, as in the published screenshots -- not env.user, which under
    # ./odev shell is OdooBot (uid 1), not Mitchell Admin.
    vals = {"user_id": admin.id, **vals}
    event = Event.search([("name", "=", name)], limit=1)
    if not event:
        event = Event.create({"name": name, "date_tz": madrid, **vals})
    else:
        event.write(vals)
    return event


def set_hosts(event, hosts):
    """hosts: [(partner, role, sequence), ...], idempotent by (event, partner)."""
    for partner, role, sequence in hosts:
        line = Host.search([("event_id", "=", event.id), ("partner_id", "=", partner.id)], limit=1)
        if line:
            line.write({"role": role, "sequence": sequence})
        else:
            Host.create(
                {
                    "event_id": event.id,
                    "partner_id": partner.id,
                    "role": role,
                    "sequence": sequence,
                }
            )


def dt(year, month, day, hour, minute=0):
    return datetime(year, month, day, hour, minute)


bootcamp = find_or_create_event(
    "Beginner's Bootcamp",
    date_begin=dt(2026, 10, 2, 18, 0),
    date_end=dt(2026, 10, 4, 14, 0),
    address_id=company.partner_id.id,
    website_published=True,
)
set_hosts(bootcamp, [(marc, "Lead Instructor", 10), (edith, "Assistant", 20)])

festival = find_or_create_event(
    "Weekend Festival",
    date_begin=dt(2026, 11, 13, 18, 0),
    date_end=dt(2026, 11, 15, 13, 0),
    address_id=company.partner_id.id,
)
set_hosts(festival, [(marc, False, 10)])

design = find_or_create_event(
    "Design Workshop",
    date_begin=dt(2026, 11, 21, 10, 0),
    date_end=dt(2026, 11, 21, 15, 0),
    address_id=company.partner_id.id,
)
set_hosts(design, [(marc, False, 10), (edith, False, 20)])

basics = find_or_create_event(
    "Back to Basics",
    date_begin=dt(2026, 11, 7, 10, 0),
    date_end=dt(2026, 11, 7, 14, 0),
    address_id=company.partner_id.id,
    vmk_deadline_custom=True,
    vmk_deadline_hours=2.0,
)
set_hosts(basics, [(edith, False, 10)])
if not basics.event_ticket_ids.filtered(lambda t: t.name == "Admission"):
    basics.write({"event_ticket_ids": [(0, 0, {"name": "Admission"})]})


# ---------------------------------------------------------------------------
# Registration Deadline setting: on, at 01:30.
# ---------------------------------------------------------------------------
settings = env["res.config.settings"].create(
    {"vmk_registration_deadline_enabled": True, "vmk_registration_deadline_hours": 1.5}
)
settings.execute()


# ---------------------------------------------------------------------------
# Rosa Vidal, with two additional addresses, her avatar, and a lead that
# arrived by email from one of them -- through the mail gateway, so the
# contact is found the way real mail finds it.
# ---------------------------------------------------------------------------
rosa = find_or_create_partner("Rosa Vidal")
rosa.write(
    {
        "email": "rosa.vidal@example.com",
        "phone": "+34 600 123 456",
        "function": "Product Designer",
        "lang": "en_GB",
        "city": "Valencia",
        "country_id": spain.id,
        "vmk_email_ids": [
            (5, 0, 0),
            (0, 0, {"email": "rosa@example.org", "label": "Personal", "sequence": 10}),
            (0, 0, {"email": "rosa.billing@example.com", "label": "Billing", "sequence": 20}),
        ],
    }
)
with open(
    "/mnt/extra-addons/odoo-addons-custom/tools/shots/demo/rosa_vidal.png", "rb"
) as f:
    rosa.image_1920 = base64.b64encode(f.read())

env["crm.lead"].search([("name", "=", "Laser cutting for a small order")]).unlink()
lead = env["crm.lead"].browse(
    env["mail.thread"].message_process(
        "crm.lead",
        """From: Rosa Vidal <rosa@example.org>
To: info@example.com
Subject: Laser cutting for a small order
Message-ID: <rosa-laser-order@example.org>
Date: Thu, 24 Sep 2026 17:42:00 +0200
Content-Type: text/html; charset=utf-8

<p>Hi, could you cut 40 coasters in 3mm birch plywood from the attached design?</p><p>Thanks,<br>Rosa</p>
""",
    )
)
tag = env["crm.tag"].search([("name", "=", "Laser Cutting")], limit=1) or env["crm.tag"].create(
    {"name": "Laser Cutting"}
)
lead.write(
    {
        "expected_revenue": 240,
        "probability": 40,
        "user_id": env.ref("base.user_admin").id,
        "date_deadline": "2026-10-16",
        "priority": "1",
        "tag_ids": [(6, 0, tag.ids)],
    }
)
assert rosa.email == "rosa.vidal@example.com" and lead.partner_id == rosa

env.registry.signal_changes()
env.cr.commit()
print("done.")


def open_studio_evening(env):
    """A published event starting within the deadline, for the public page capture.

    Time-dependent by nature: call this on its own, right before capturing, not as part of the
    main seed. See the module docstring above for the one-liner.
    """
    start = (datetime.now() + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    existing = env["event.event"].search([("name", "=", "Open Studio Evening")])
    existing.unlink()
    event = env["event.event"].create(
        {
            "name": "Open Studio Evening",
            "date_begin": start,
            "date_end": start + timedelta(hours=3),
            "date_tz": "Europe/Madrid",
            "website_published": True,
            "description": "<p>A drop-in evening in the studio: bring a project, use the "
            "printers, and get help from the team.</p>",
            "event_ticket_ids": [(0, 0, {"name": "Admission"})],
        }
    )
    env.registry.signal_changes()
    env.cr.commit()
    print("Open Studio Evening recreated, starting", start)
    return event
