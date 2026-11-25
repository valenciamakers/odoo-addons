# /// script
# requires-python = ">=3.11"
# dependencies = ["playwright>=1.50"]
# ///
"""Event Series (Website): a series' page, the /event listing's Series filter, and an event page's
link to its series, all as a visitor sees them.

Writes main_screenshot.png, series_filter.png, and event_link.png. The page's backend image,
series_form.png, comes from the vmk_event_series recipe.
"""
import asyncio, sys
from pathlib import Path
from playwright.async_api import async_playwright
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import shots

SERIES = "Intro to 3D Printing"


async def main(out):
    async with async_playwright() as p:
        tab = await shots.backend_tab(p, scale=1)
        await shots.goto(tab, shots.BASE + "/odoo")
        series = await shots.record_id(tab, "vmk.event.series", SERIES)
        url = (await shots.rpc(tab, "vmk.event.series", "read", [[series], ["website_url"]]))[0]["website_url"]
        event = (await shots.rpc(tab, "event.event", "search", [[["series_id", "=", series]]],
                                 {"limit": 1, "order": "date_begin desc"}))[0]
        event_url = (await shots.rpc(tab, "event.event", "read", [[event], ["website_url"]]))[0]["website_url"]

        page = await shots.public_page(p)
        # the series' page, from the header to the end of its dates
        await shots.goto(page, shots.BASE + url)
        events = await page.locator("#o_wevent_index_main_col").bounding_box()
        await page.screenshot(path=out / "main_screenshot.png", full_page=True,
                              clip={"x": 0, "y": 0, "width": 1280, "height": events["y"] + events["height"]})
        # the listing, with the Series filter open
        await shots.goto(page, shots.BASE + "/event")
        toggle = page.locator(".o_vmk_event_series_filter .dropdown-toggle")
        await toggle.click()
        item = page.locator(".o_vmk_event_series_filter .dropdown-menu .dropdown-item", has_text=SERIES)
        await item.wait_for()
        box = await item.bounding_box()
        x, y = box["x"] + 40, box["y"] + box["height"] / 2
        await page.mouse.move(x, y, steps=6); await page.wait_for_timeout(400)
        await page.evaluate(shots.CURSOR, [x - 1, y - 1])
        await page.screenshot(path=out / "series_filter.png", clip={"x": 0, "y": 0, "width": 1280, "height": 460})
        # an event's page: its sidebar, from the date to the series' link
        await shots.goto(page, shots.BASE + event_url)
        link = page.locator(".o_vmk_event_series_link")
        await link.wait_for()
        block = await link.bounding_box()
        top = await link.evaluate("el => el.parentElement.getBoundingClientRect().top")  # the sidebar
        await page.screenshot(path=out / "event_link.png",
                              clip={"x": block["x"] - 24, "y": top + 2,  # clear of the header
                                    "width": block["width"] + 48, "height": block["y"] + block["height"] - top - 2})
    return out


if __name__ == "__main__":
    out = shots.out_dir("vmk_website_event_series", sys.argv)
    asyncio.run(main(out)); print("wrote", out)
