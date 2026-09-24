# /// script
# requires-python = ">=3.11"
# dependencies = ["playwright>=1.50"]
# ///
"""Protect Language Edits: a language form with an edit protected from updates.

Writes main_screenshot.png. Sets Catalan's ISO code to `ca`, the README's example edit, which the
module protects on the spot.
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
        ids = await shots.rpc(page, "res.lang", "search", [[["code", "=", "ca_ES"]]])
        await shots.rpc(page, "res.lang", "write", [ids, {"iso_code": "ca"}])
        await shots.open_backend(page, f"/odoo/action-base.res_lang_act_window/{ids[0]}?debug=1", wait=".o_form_view", extra_css=_sorting.HIDE)
        await shots.park_mouse(page, 1280, 800)
        sheet = await page.locator(".o_form_sheet").first.bounding_box()
        await page.screenshot(path=out / "main_screenshot.png", clip={"x": 0, "y": 0, "width": 1280, "height": sheet["y"] + sheet["height"] + 16})
        await page.goto(shots.BASE + "/odoo?debug=", wait_until="networkidle")
    print("wrote", out)


if __name__ == "__main__":
    asyncio.run(main(shots.out_dir("vmk_language_freeze_meta", sys.argv)))
