# /// script
# requires-python = ">=3.11"
# dependencies = ["playwright>=1.50"]
# ///
"""Multiple Contact Emails: a contact's Additional Emails tab, and a lead matched from one of them.

Writes main_screenshot.png and lead.png to the module, and the cover's cut-out
vmk_partner_email_multiple_emails.png to tools/covers/img/.
The demo data is in tools/shots/README.md.
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
# capture-only, for the cover: the field groups between the contact's name and the tabs
COVER_CSS = " .o_form_sheet .o_group { display: none !important; }"
# capture-only, for the lead: its Notes and Contacts tabs, between the rows and the message, and
# the empty Properties row under them; and the form's two groups side by side, as above
# Bootstrap's lg breakpoint, rather than stacked
LEAD_CSS = """ .o_form_sheet .o_notebook { display: none !important; }
    .o_form_sheet > .d-flex:has(> .o_field_widget[name=lead_properties]) { display: none !important; }
    .o_form_sheet .o_group.row > .o_inner_group.col-lg-6 { flex: 0 0 auto !important; width: 50% !important; }"""


async def sharp_avatar(page):
    """Capture-only: the form shows the 128px preview (preview_image: avatar_128 in base's partner
    form), which a 2x capture scales up and blurs; load the 1024px one in its place."""
    await page.evaluate("""() => Promise.all([...document.querySelectorAll('.oe_avatar img')].map(img => {
        if (!img.src.includes('avatar_128')) return;
        img.src = img.src.replace('avatar_128', 'avatar_1024');
        return img.decode(); }))""")
    await page.wait_for_timeout(300)


async def main(out, parts):
    async with async_playwright() as p:
        page = await shots.backend_tab(p, width=1280, height=900)
        await page.goto(shots.BASE + "/odoo", wait_until="networkidle")
        await page.wait_for_selector(".o_home_menu, .o_main_navbar")
        # the contact, on the Additional Emails tab, down to the end of the form sheet
        contact = await shots.record_id(page, "res.partner", CONTACT)
        await shots.open_backend(page, f"/odoo/contacts/{contact}", extra_css=NO_SCROLLBAR)
        await page.locator(".o_notebook .nav-link[name=vmk_additional_emails]").first.click(); await page.wait_for_timeout(700)
        await sharp_avatar(page)
        await shots.polish(page); await shots.park_mouse(page, 1280, 900)
        sheet = await page.locator(".o_form_sheet").first.bounding_box()
        await page.screenshot(path=out / "main_screenshot.png", clip={"x": 0, "y": 0, "width": 1280, "height": sheet["y"] + sheet["height"] + 5})
        # cover part: the contact's name and primary address above the Additional Emails list,
        # narrower so the columns sit close, with the field groups between them hidden
        await page._vmk_cdp.send("Emulation.setDeviceMetricsOverride",
                                 {"width": 620, "height": 900, "deviceScaleFactor": 2, "mobile": False})
        await shots.open_backend(page, f"/odoo/contacts/{contact}", extra_css=NO_SCROLLBAR + COVER_CSS)
        await page.locator(".o_notebook .nav-link[name=vmk_additional_emails]").first.click(); await page.wait_for_timeout(700)
        await sharp_avatar(page)
        await shots.polish(page); await shots.park_mouse(page, 620, 900)
        sheet = await page.locator(".o_form_sheet").first.bounding_box()
        add = await page.locator(".o_notebook .o_field_x2many_list_row_add").first.bounding_box()
        await page.screenshot(path=parts / "vmk_partner_email_multiple_emails.png", clip={
            "x": sheet["x"], "y": sheet["y"], "width": sheet["width"], "height": add["y"] + add["height"] - sheet["y"] + 1})
        # the lead, its contact found from the address the mail came from: narrow enough for the
        # chatter to fall below the form, with the tabs hidden so the message sits under the rows
        await page._vmk_cdp.send("Emulation.setDeviceMetricsOverride",
                                 {"width": 900, "height": 1000, "deviceScaleFactor": 2, "mobile": False})
        lead = await shots.record_id(page, "crm.lead", LEAD)
        await shots.open_backend(page, f"/odoo/crm/{lead}", extra_css=NO_SCROLLBAR + LEAD_CSS)
        await page.wait_for_selector(".o-mail-Message"); await page.wait_for_timeout(500)
        await shots.polish(page); await shots.park_mouse(page, 900, 1000)
        message = await page.locator(".o-mail-Message").first.bounding_box()
        await page.screenshot(path=out / "lead.png", clip={"x": 0, "y": 0, "width": 900, "height": message["y"] + message["height"] + 16})
    print("wrote", out)


if __name__ == "__main__":
    out = shots.out_dir("vmk_partner_email_multiple", sys.argv)
    parts = out if "--out" in sys.argv else Path(__file__).resolve().parent.parent.parent / "covers" / "img"
    asyncio.run(main(out, parts))
