# /// script
# requires-python = ">=3.11"
# dependencies = ["playwright>=1.50"]
# ///
"""Double Opt-In for Email Marketing: the consent log, a contact's subscriptions with one awaiting
confirmation, the confirmation email, and the page its link opens.

Writes main_screenshot.png, subscriptions.png, email.png, and confirm_page.png. Expects the demo's
mailing lists and subscribers (README.md), whose seed leaves Jordi Puig awaiting confirmation and
his link in the `shots.double_optin_confirm_url` system parameter. The email is read from the
stack's Mailpit, at MAILPIT_URL (the stack's port +2, http://localhost:1902 by default).
"""
import asyncio, json, os, sys, urllib.parse, urllib.request
from pathlib import Path
from playwright.async_api import async_playwright
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import shots

MAILPIT = os.environ.get("MAILPIT_URL", "http://localhost:1902")
PENDING = "Jordi Puig"
# capture-only: the Reason column, empty in the demo, hidden, and the table laid out again to fill
# the width it leaves
LOG_CSS = """th[data-name="reason"], td[name="reason"] { display: none !important; }
    .o_list_renderer .o_list_table { table-layout: auto !important; width: 100% !important; }
    .o_list_renderer .o_list_table th { width: auto !important; }"""


def latest_email(to):
    query = urllib.parse.quote(f'to:"{to}"')
    with urllib.request.urlopen(f"{MAILPIT}/api/v1/search?query={query}&limit=1", timeout=30) as r:
        messages = json.load(r)["messages"]
    if not messages:
        raise SystemExit(f"no email to {to} in {MAILPIT}: re-run the demo seed (README.md)")
    return messages[0]["ID"]


async def main(out):
    async with async_playwright() as p:
        page = await shots.backend_tab(p)
        await shots.goto(page, shots.BASE + "/odoo")
        contact = (await shots.rpc(page, "mailing.contact", "search", [[["name", "=", PENDING]]], {"limit": 1}))[0]
        email = (await shots.rpc(page, "mailing.contact", "read", [[contact], ["email"]]))[0]["email"]
        url = (await shots.rpc(page, "ir.config_parameter", "search_read",
                               [[["key", "=", "shots.double_optin_confirm_url"]]], {"fields": ["value"]}))[0]["value"]
        # the consent log
        await shots.open_backend(page, "/odoo/action-vmk_mass_mailing_double_optin.vmk_mailing_consent_log_action",
                                 extra_css=LOG_CSS)
        await shots.park_mouse(page, 1280, 800)
        table = await page.locator(".o_list_table").bounding_box()
        await page.screenshot(path=out / "main_screenshot.png",
                              clip={"x": 0, "y": 44, "width": 1280, "height": table["y"] + table["height"] + 16 - 44})
        # a contact's subscriptions, one awaiting confirmation, the pointer on Resend Confirmation; in
        # a window 1200px wide, where the form's text stays readable at the page's width, its
        # fields still sit in two columns, and Odoo 19's wider Subscriptions list (it has an
        # unsubscription date and a reason, which 20's lacks) does not truncate its columns
        await page.set_viewport_size({"width": 1200, "height": 800})
        await shots.open_backend(page, f"/odoo/mailing.contact/{contact}")
        tab = page.locator(".o_notebook .nav-link", has_text="Subscriptions")
        if await tab.count():
            await tab.first.click(); await page.wait_for_timeout(500)
        field = page.locator("div[name=subscription_ids]")
        await field.wait_for()
        resend = field.locator("button[name=action_vmk_request_confirmation]:visible").first
        rbox = await resend.bounding_box()
        x, y = rbox["x"] + rbox["width"] * 0.5, rbox["y"] + rbox["height"] * 0.6
        await page.mouse.move(x, y, steps=6); await page.wait_for_timeout(1200)
        await page.evaluate(shots.CURSOR, [x - 1, y - 1])
        sheet = await page.locator(".o_form_sheet").bounding_box()
        add = await field.locator(".o_field_x2many_list_row_add").bounding_box()  # the list's last row
        await page.screenshot(path=out / "subscriptions.png",
                              clip={"x": sheet["x"], "y": sheet["y"], "width": sheet["width"],
                                    "height": add["y"] + add["height"] + 16 - sheet["y"]})
        # the confirmation email, as Mailpit shows its HTML
        mail = await shots.public_page(p, width=760, height=900)
        await shots.goto(mail, f"{MAILPIT}/view/{latest_email(email)}.html")
        body = await mail.locator("body table").first.bounding_box()  # the email's outer table
        await mail.screenshot(path=out / "email.png",
                              clip={"x": 0, "y": 0, "width": 760, "height": body["y"] + body["height"] + 8})
        # the page the email's link opens, core's mailing page layout: its message box, without the
        # company logo above it, which the demo company lacks
        public = await shots.public_page(p)
        await shots.goto(public, url)
        box = await public.locator(".alert").first.bounding_box()
        await public.screenshot(path=out / "confirm_page.png",
                                clip={"x": box["x"] - 24, "y": box["y"] - 24, "width": box["width"] + 48, "height": box["height"] + 48})
    return out


if __name__ == "__main__":
    out = shots.out_dir("vmk_mass_mailing_double_optin", sys.argv)
    asyncio.run(main(out)); print("wrote", out)
