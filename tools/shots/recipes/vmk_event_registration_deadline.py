# /// script
# requires-python = ">=3.11"
# dependencies = ["playwright>=1.50"]
# ///
"""Event Registration Deadline: a public event page showing Registrations Closed, the setting, and an
event's own deadline.

Writes main_screenshot.png, deadline_settings.png, and deadline_event.png. The public page needs a
published event whose start is within the deadline; see README.md.
"""
import asyncio, sys
from pathlib import Path
from playwright.async_api import async_playwright
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import shots

CLOSED_EVENT = "Open Studio Evening"   # published, starting within the deadline
OWN_DEADLINE = "Back to Basics"        # has its own 02:00 deadline and an Admission ticket
FORM_CSS = """
    .o_inner_group > .o_cell:has([name=vmk_host_names]),
    .o_inner_group > .o_cell:has(+ .o_cell [name=vmk_host_names]) { display: none !important; }
    .o_field_widget[name=address_id] .o_field_many2one_extra { display: none !important; }
    .o_notebook .nav-item:has(.nav-link[name=vmk_hosts]) { display: none !important; }"""


async def main(out):
    async with async_playwright() as p:
        page = await shots.backend_tab(p, width=1280, height=900)
        await page.goto(shots.BASE + "/odoo", wait_until="networkidle")
        closed = await shots.record_id(page, "event.event", CLOSED_EVENT)
        own = await shots.record_id(page, "event.event", OWN_DEADLINE)
        url = (await shots.rpc(page, "event.event", "read", [[closed], ["website_url"]]))[0]["website_url"]
        # the Registration section of the Events settings
        await shots.open_backend(page, "/odoo/settings#event", wait="#vmk_registration_deadline")
        await shots.park_mouse(page, 1280, 900)
        head = await page.locator(".app_settings_block h2", has_text="Registration").first.bounding_box()
        box = await page.locator("#vmk_registration_deadline").bounding_box()
        await page.screenshot(path=out / "deadline_settings.png", clip={
            "x": head["x"], "y": head["y"], "width": 1280 - head["x"], "height": box["y"] + box["height"] - head["y"] + 31})
        # an event's own deadline: the right-hand group of its form
        await shots.open_backend(page, f"/odoo/events/{own}", extra_css=FORM_CSS)
        await shots.park_mouse(page, 1280, 900)
        grp = await page.locator(".o_inner_group:has([name=vmk_deadline_custom])").first.bounding_box()
        await page.screenshot(path=out / "deadline_event.png", clip={
            "x": grp["x"] + 2, "y": grp["y"] - 13, "width": 429, "height": grp["height"] + 16})
        # the public page, closed: space above the breadcrumb, and no rule under the calendar buttons
        pub = await shots.public_page(p, height=900)
        await pub.goto(shots.BASE + url, wait_until="networkidle")
        await pub.add_style_tag(content=".o_wevent_bordered_block { border-bottom: 0 !important; }")
        await pub.wait_for_timeout(500)
        await pub.screenshot(path=out / "main_screenshot.png", clip={"x": 70, "y": 63, "width": 1140, "height": 407})


if __name__ == "__main__":
    out = shots.out_dir("vmk_event_registration_deadline", sys.argv)
    asyncio.run(main(out)); print("wrote", out)
