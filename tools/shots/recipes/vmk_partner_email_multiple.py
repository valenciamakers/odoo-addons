# /// script
# requires-python = ">=3.11"
# dependencies = ["playwright>=1.50"]
# ///
"""Multiple Contact Emails: a contact's Additional Emails tab, and a lead matched from one of them.

Writes main_screenshot.png and lead.png to the module. The demo data is in tools/shots/README.md.
"""
import asyncio, sys
from pathlib import Path
from playwright.async_api import async_playwright
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import shots

CONTACT = "Rosa Vidal"
LEAD = "Laser cutting for a small order"
# capture-only: the form scrolls, and its scrollbar would show at the right edge
NO_SCROLLBAR = "* { scrollbar-width: none !important; }"


async def main(out):
    async with async_playwright() as p:
        page = await shots.backend_tab(p, width=1280, height=900)
        await page.goto(shots.BASE + "/odoo", wait_until="networkidle")
        await page.wait_for_selector(".o_home_menu, .o_main_navbar")
        # the contact, on the Additional Emails tab, down to the end of the form sheet
        contact = await shots.record_id(page, "res.partner", CONTACT)
        await shots.open_backend(page, f"/odoo/contacts/{contact}", extra_css=NO_SCROLLBAR)
        await page.locator(".o_notebook .nav-link[name=vmk_additional_emails]").first.click(); await page.wait_for_timeout(700)
        await shots.polish(page); await shots.park_mouse(page, 1280, 900)
        sheet = await page.locator(".o_form_sheet").first.bounding_box()
        await page.screenshot(path=out / "main_screenshot.png", clip={"x": 0, "y": 0, "width": 1280, "height": sheet["y"] + sheet["height"] + 5})
        # the lead, its contact found from the address the mail came from; wide enough for the
        # chatter to sit beside the form, and down to the end of the message
        await page._vmk_cdp.send("Emulation.setDeviceMetricsOverride",
                                 {"width": 1600, "height": 900, "deviceScaleFactor": 2, "mobile": False})
        lead = await shots.record_id(page, "crm.lead", LEAD)
        await shots.open_backend(page, f"/odoo/crm/{lead}")
        await page.wait_for_selector(".o-mail-Message"); await page.wait_for_timeout(500)
        await shots.polish(page); await shots.park_mouse(page, 1600, 900)
        message = await page.locator(".o-mail-Message").first.bounding_box()
        phone = await page.locator(".o_form_sheet .o_field_widget[name=phone]").first.bounding_box()
        bottom = max(message["y"] + message["height"], phone["y"] + phone["height"]) + 16
        await page.screenshot(path=out / "lead.png", clip={"x": 0, "y": 0, "width": 1600, "height": bottom})
    print("wrote", out)


if __name__ == "__main__":
    asyncio.run(main(shots.out_dir("vmk_partner_email_multiple", sys.argv)))
