# /// script
# requires-python = ">=3.11"
# dependencies = ["playwright>=1.50"]
# ///
"""Multi-Day Event Slots: the slot calendar with a multi-day slot open and hovered, and the slot form.

Writes main_screenshot.png and slot_form.png, and copies main_screenshot.png to Multi-Day Event
Slots (Website) as slot_calendar.png, which that page and its cover show.
"""
import asyncio, shutil, sys
from pathlib import Path
from playwright.async_api import async_playwright
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import shots

EVENT = "Beginner's Bootcamp"
# capture-only: the popover sized to its title, with room for 20's close icon, which sits over the
# header's end; and today's marker off, since it lands in the month shown (the 19 shots predate it)
CAL_CSS = """
    .o_cw_popover { width: max-content !important; }
    .o_cw_popover .o_popover_header { padding-right: 3rem !important; }
    .fc-day-today .fc-daygrid-day-number { background: none !important; color: inherit !important; }
    .o_datetime_picker .o_date_item_cell.o_today, .o_datetime_picker .o_date_item_cell.o_today > div {
        background: none !important; color: inherit !important; font-weight: normal !important; }"""


async def main(out):
    async with async_playwright() as p:
        page = await shots.backend_tab(p)
        await shots.goto(page, shots.BASE + "/odoo")
        event = await shots.record_id(page, "event.event", EVENT)
        slot = (await shots.rpc(page, "event.slot", "search_read", [[["event_id", "=", event]]],
                                {"fields": ["id", "date"], "order": "start_datetime", "limit": 1}))[0]
        # calendar: the popover sized to its title
        await shots.open_backend(page, f"/odoo/events/{event}", extra_css=CAL_CSS)
        await page.click("button[name=action_open_slot_calendar]")
        bar = page.locator(f".fc-event[data-event-id='{slot['id']}']").first
        await bar.wait_for(); await shots.polish(page)
        await shots.day_cell(page, int(slot["date"][-2:])).click(); await page.wait_for_timeout(600)
        box = await bar.bounding_box()
        await page.mouse.click(box["x"] + 60, box["y"] + box["height"] / 2)
        await page.wait_for_selector(".o_popover")
        x, y = box["x"] + box["width"] * 0.62, box["y"] + box["height"] / 2
        await page.mouse.move(x, y, steps=8); await page.wait_for_timeout(600)
        await page.evaluate(shots.CURSOR, [x - 1, y - 1])
        await page.screenshot(path=out / "main_screenshot.png")
        await page.evaluate("document.getElementById('vmk-cursor')?.remove()")
        # slot form: held to 760px with the range at its natural width, cropped to its first rows
        await shots.open_backend(page, f"/odoo/events/{event}/event.slot/{slot['id']}", extra_css="""
            .o_form_renderer.o_form_nosheet { max-width: 760px; }
            .o_field_vmk_event_slot_daterange .o_daterange_start,
            .o_field_vmk_event_slot_daterange .o_daterange_end { width: auto !important; }""")
        await shots.park_mouse(page, 1280, 800)
        await page.screenshot(path=out / "slot_form.png", clip={"x": 0, "y": 44, "width": 700, "height": 156})
    return out


if __name__ == "__main__":
    out = shots.out_dir("vmk_event_slot_multiday", sys.argv)
    asyncio.run(main(out))
    if "--out" not in sys.argv:
        shutil.copyfile(out / "main_screenshot.png",
                        out.parent.parent.parent / "vmk_website_event_slot_multiday/static/description/slot_calendar.png")
    print("wrote", out)
