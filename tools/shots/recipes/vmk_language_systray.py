# /// script
# requires-python = ">=3.11"
# dependencies = ["playwright>=1.50"]
# ///
"""Backend Language Menu: the systray's language menu, open.

Writes main_screenshot.png (the whole window) and menu.png (the systray and menu alone).
"""
import asyncio, sys
from pathlib import Path
from playwright.async_api import async_playwright
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import _sorting, shots


async def main(out):
    async with async_playwright() as p:
        page = await shots.backend_tab(p, width=1280, height=800)
        await _sorting.ready(page)
        await page.goto(shots.BASE + "/odoo?debug=", wait_until="networkidle")
        await page.wait_for_selector(".o_home_menu .o_app"); await page.wait_for_timeout(800)
        await shots.polish(page, _sorting.HIDE)
        await page.locator(".o_vmk_language_systray button").first.click(); await page.wait_for_timeout(700)
        btn = await page.locator(".o_vmk_language_systray button").first.bounding_box()
        x, y = btn["x"] + btn["width"] - 11, btn["y"] + btn["height"] - 10  # the arrow's tip on the globe, as if clicking it
        await page.mouse.move(x, y); await page.wait_for_timeout(300)
        await page.evaluate(shots.CURSOR, [x, y])
        await page.screenshot(path=out / "main_screenshot.png")
        # the crop is the systray and menu alone: hide the app grid so no icon peeks out beside the menu
        await page.add_style_tag(content=".o_home_menu .o_apps { visibility: hidden !important; }"); await page.wait_for_timeout(200)
        menu = await page.locator(".o-dropdown--menu").first.bounding_box()
        x0 = menu["x"] - 8  # the menu and the systray above it, clear of the app icons behind
        await page.screenshot(path=out / "menu.png", clip={"x": x0, "y": 0, "width": 1280 - x0, "height": menu["y"] + menu["height"] + 8})
        await page.evaluate("document.getElementById('vmk-cursor')?.remove()")
    print("wrote", out)


if __name__ == "__main__":
    asyncio.run(main(shots.out_dir("vmk_language_systray", sys.argv)))
