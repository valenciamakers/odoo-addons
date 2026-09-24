# /// script
# requires-python = ">=3.11"
# dependencies = ["playwright>=1.50"]
# ///
"""Event Hosts: the event form's Hosts tab, the events list grouped by host, and two cover parts.

Writes main_screenshot.png and hosts_by_host.png to the module, and the cover's cut-outs
vmk_event_host_summary.png and vmk_event_host_list.png to tools/covers/img/.
"""
import asyncio, sys
from pathlib import Path
from playwright.async_api import async_playwright
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import shots

EVENT = "Beginner's Bootcamp"
# capture-only: hide the deadline module's field and the venue's address, and show the read-only
# Hosts label at full strength
FORM_CSS = """
    .o_inner_group > .o_cell:has([name=vmk_deadline_custom]),
    .o_inner_group > .o_cell:has(+ .o_cell [name=vmk_deadline_custom]) { display: none !important; }
    .o_field_widget[name=address_id] .o_field_many2one_extra { display: none !important; }
    label[for^='vmk_host_names'].o_form_label_readonly { opacity: 1 !important; }"""
LIST_CSS = """
    .o_list_view [data-name=address_id], .o_list_view [name=address_id],
    .o_list_view [data-name=seats_taken], .o_list_view [name=seats_taken],
    .o_list_view [data-name=seats_used], .o_list_view [name=seats_used] { display: none !important; }
    .o_list_view .o_list_table { table-layout: auto !important; width: 100% !important; }
    .o_list_view .o_list_table thead th { width: auto !important; max-width: none !important; }
    .o_list_view .o_data_cell { max-width: none !important; white-space: nowrap; }"""


async def event_form(page, event, width):
    await page._vmk_cdp.send("Emulation.setDeviceMetricsOverride",
                             {"width": width, "height": 920, "deviceScaleFactor": 2, "mobile": False})
    await shots.open_backend(page, f"/odoo/events/{event}", extra_css=FORM_CSS)
    await page.locator(".o_notebook .nav-link[name=vmk_hosts]").first.click(); await page.wait_for_timeout(700)
    await shots.polish(page); await shots.park_mouse(page, width, 920)


async def main(out, parts):
    async with async_playwright() as p:
        page = await shots.backend_tab(p, width=1280, height=920)
        await page.goto(shots.BASE + "/odoo", wait_until="networkidle")
        event = await shots.record_id(page, "event.event", EVENT)
        # the form, down to the Hosts tab's "Add a line"
        await event_form(page, event, 1280)
        add = await page.locator(".o_notebook .o_field_x2many_list_row_add").first.bounding_box()
        await page.screenshot(path=out / "main_screenshot.png", clip={"x": 0, "y": 0, "width": 1280, "height": add["y"] + add["height"] + 14})
        # cover part: the Organizer, Responsible, and Hosts rows
        org = await page.locator(".o_inner_group .o_cell:has([name=organizer_id])").first.bounding_box()
        hosts = await page.locator(".o_inner_group .o_cell:has([name=vmk_host_names])").first.bounding_box()
        x0, y0 = org["x"] - 150, org["y"] - 12
        await page.screenshot(path=parts / "vmk_event_host_summary.png", clip={
            "x": x0, "y": y0, "width": hosts["x"] + hosts["width"] - x0 + 12, "height": hosts["y"] + hosts["height"] - y0 + 6})
        # cover part: the tabs and the Hosts list, narrower so the columns sit close
        await event_form(page, event, 760)
        nb = await page.locator(".o_notebook").first.bounding_box()
        last = await page.locator(".o_notebook .o_data_row").last.bounding_box()
        await page.screenshot(path=parts / "vmk_event_host_list.png", clip={
            "x": nb["x"], "y": nb["y"], "width": nb["width"], "height": last["y"] + last["height"] - nb["y"] + 9})
        # the events list grouped by host, with the optional Hosts column shown
        await page._vmk_cdp.send("Emulation.setDeviceMetricsOverride",
                                 {"width": 1100, "height": 800, "deviceScaleFactor": 2, "mobile": False})
        await shots.open_backend(page, "/odoo/events?view_type=list", wait=".o_list_view", extra_css=LIST_CSS)
        await page.click(".o_optional_columns_dropdown_toggle"); await page.wait_for_timeout(400)
        item = page.locator(".o-dropdown--menu .dropdown-item", has_text="Hosts").first
        if not await item.locator("input:checked").count():
            await item.click(); await page.wait_for_timeout(400)
        await page.keyboard.press("Escape")
        await page.click(".o_searchview_dropdown_toggler"); await page.wait_for_timeout(500)
        await page.locator(".o_group_by_menu .o-dropdown-item, .o_group_by_menu .dropdown-item", has_text="Host").first.click()
        await page.wait_for_timeout(800); await page.keyboard.press("Escape")
        for g in await page.locator(".o_group_header").all():
            await g.click(); await page.wait_for_timeout(500)
        await shots.polish(page); await shots.park_mouse(page, 1100, 800)
        bottom = await page.evaluate("document.querySelector('.o_list_table').getBoundingClientRect().bottom")
        await page.screenshot(path=out / "hosts_by_host.png", clip={"x": 0, "y": 0, "width": 1100, "height": bottom + 1})


if __name__ == "__main__":
    out = shots.out_dir("vmk_event_host", sys.argv)
    parts = out if "--out" in sys.argv else Path(__file__).resolve().parent.parent.parent / "covers" / "img"
    asyncio.run(main(out, parts)); print("wrote", out, "and", parts)
