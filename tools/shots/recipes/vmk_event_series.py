# /// script
# requires-python = ">=3.11"
# dependencies = ["playwright>=1.50"]
# ///
"""Event Series: a series' form, and the events list grouped by series.

Writes main_screenshot.png and events_by_series.png, and copies main_screenshot.png to Event Series
(Website) as series_form.png, which that module's cover shows.
"""
import asyncio, shutil, sys
from pathlib import Path
from playwright.async_api import async_playwright
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import shots

SERIES = "Intro to 3D Printing"
# capture-only: the form held to a width its fields fill, as on a narrower screen
FORM_CSS = ".o_form_view .o_form_sheet_bg { max-width: 960px; }"
# capture-only: the list's venue, responsible, and attendee columns hidden, so the event and series
# names have room; the view switcher and pager, which on 19 run wider than the rows; and the group
# with no series, which only the demo's other events fill, left out
HIDDEN = ["address_id", "user_id", "seats_taken", "seats_expected", "seats_used", "seats_reserved"]
LIST_CSS = "".join(f'th[data-name="{n}"], td[name="{n}"] {{ display: none !important; }}' for n in HIDDEN) + """
    .o_cp_switch_buttons, .o_cp_pager { display: none !important; }
    .o_list_renderer .o_list_table { table-layout: auto !important; width: 100% !important; }
    .o_list_renderer .o_list_table th { width: auto !important; }
    .o_list_table tr.o_group_header:has(+ tr:not(.o_data_row)):last-of-type,
    .o_list_table tbody tr.o_group_header:last-child { display: none !important; }"""


async def main(out):
    async with async_playwright() as p:
        page = await shots.backend_tab(p)
        await shots.goto(page, shots.BASE + "/odoo")
        series = await shots.record_id(page, "vmk.event.series", SERIES)
        # the form, with the pointer on New Event in Series
        await shots.open_backend(page, f"/odoo/event-series/{series}", extra_css=FORM_CSS)
        button = page.locator("button[name=action_new_event]")
        box = await button.bounding_box()
        x, y = box["x"] + box["width"] * 0.7, box["y"] + box["height"] * 0.65
        await page.mouse.move(x, y, steps=6); await page.wait_for_timeout(500)
        await page.evaluate(shots.CURSOR, [x - 1, y - 1])
        sheet = await page.locator(".o_form_sheet").bounding_box()
        await page.screenshot(path=out / "main_screenshot.png",
                              clip={"x": 0, "y": 44, "width": 984, "height": sheet["y"] + sheet["height"] + 16 - 44})
        await page.evaluate("document.getElementById('vmk-cursor')?.remove()")
        # the events list, grouped by series, both groups open
        await shots.open_backend(page, "/odoo/events?view_type=list", extra_css=LIST_CSS)
        await page.click(".o_searchview_dropdown_toggler")
        await page.locator(".o_group_by_menu .o-dropdown-item", has_text="Series").first.click()
        await page.wait_for_selector(".o_group_header")
        await page.keyboard.press("Escape")
        for name in [SERIES, "Laser Cutting Basics"]:
            await page.locator(".o_group_header", has_text=name).first.click()
            await page.wait_for_timeout(600)
        await shots.polish(page)
        await shots.park_mouse(page, 1280, 800)
        table = await page.locator(".o_list_table").bounding_box()
        await page.screenshot(path=out / "events_by_series.png",
                              clip={"x": 0, "y": 44, "width": 1225,  # to the rows' end: past it the list's own background shows
                                    "height": table["y"] + table["height"] - 44})
    return out


if __name__ == "__main__":
    out = shots.out_dir("vmk_event_series", sys.argv)
    asyncio.run(main(out))
    if "--out" not in sys.argv:
        shutil.copyfile(out / "main_screenshot.png",
                        out.parent.parent.parent / "vmk_website_event_series/static/description/series_form.png")
    print("wrote", out)
