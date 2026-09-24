# /// script
# requires-python = ">=3.11"
# dependencies = ["playwright>=1.50"]
# ///
"""Multi-Day Event Slots (Website): the public registration window with a multi-day slot selected.

Writes main_screenshot.png. The page's calendar image, slot_calendar.png, comes from the
vmk_event_slot_multiday recipe.
"""
import asyncio, sys
from pathlib import Path
from playwright.async_api import async_playwright
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import shots

EVENT = "Beginner's Bootcamp"
PACK = """
    #modal_slot_registration .modal-dialog { max-width: fit-content; }
    #modal_slot_registration .o_wevent_slot_dates { display: flex; flex-wrap: nowrap; gap: 16px; }
    #modal_slot_registration .o_wevent_slot_date { flex: 0 0 auto; width: auto; }
    #modal_slot_registration .o_wevent_slot_date time.pe-5 { padding-right: 0 !important; margin-right: 0 !important; }"""


async def main(out):
    async with async_playwright() as p:
        tab = await shots.backend_tab(p, scale=1)
        await tab.goto(shots.BASE + "/odoo", wait_until="networkidle")
        event = await shots.record_id(tab, "event.event", EVENT)
        url = (await shots.rpc(tab, "event.event", "read", [[event], ["website_url"]]))[0]["website_url"]
        page = await shots.public_page(p)
        await page.goto(shots.BASE + url.rstrip("/") + "/register", wait_until="networkidle")
        await page.locator("button[data-bs-target='#modal_slot_registration']:visible").first.click()
        await page.wait_for_selector("#modal_slot_registration .o_wevent_slot_btn", state="visible")
        await page.wait_for_timeout(800)
        # capture-only: the window packed to its dates, and titled "Event Slots"
        await page.add_style_tag(content=PACK)
        await page.evaluate("document.querySelector('#modal_slot_registration .o_wevent_registration_title').textContent = 'Event Slots'")
        btn = page.locator("#modal_slot_registration .o_wevent_slot_btn:visible").first
        await btn.click(); await page.wait_for_timeout(800)
        box = await btn.bounding_box()
        x, y = box["x"] + box["width"] - 6, box["y"] + box["height"] - 5
        await page.mouse.move(x, y); await page.wait_for_timeout(400)
        await page.evaluate(shots.CURSOR, [x - 1, y - 1])
        m = await page.locator("#modal_slot_registration .modal-content").bounding_box()
        pad = 16
        await page.screenshot(path=out / "main_screenshot.png",
                              clip={"x": m["x"] - pad, "y": m["y"] - pad, "width": m["width"] + 2 * pad, "height": m["height"] + 2 * pad})


if __name__ == "__main__":
    out = shots.out_dir("vmk_website_event_slot_multiday", sys.argv)
    asyncio.run(main(out)); print("wrote", out)
