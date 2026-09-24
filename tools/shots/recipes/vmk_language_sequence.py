# /// script
# requires-python = ">=3.11"
# dependencies = ["playwright>=1.50"]
# ///
"""Language Sequence: the Languages list with drag handles in a chosen order, and the website's
language selector before and after.

Writes main_screenshot.png, selector_before.png, and selector_after.png. Uninstalls the module for
the "before" capture, installs it again, and sets ORDER; see _sorting.py.
"""
import asyncio, sys
from pathlib import Path
from playwright.async_api import async_playwright
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import _sorting, shots

ORDER = ["es_ES", "ca_ES", "en_GB", "en_US", "fr_FR", "de_DE"]  # a Valencia business's order
PAD = 12


async def selector(p, out, name):
    """The website header's language dropdown, open, cropped to it."""
    pub = await shots.public_page(p)
    await pub.goto(shots.BASE + "/", wait_until="networkidle")
    await pub.locator("header .js_language_selector .dropdown-toggle").first.click(); await pub.wait_for_timeout(600)
    t = await pub.locator("header .js_language_selector .dropdown-toggle").first.bounding_box()
    m = await pub.locator("header .js_language_selector .dropdown-menu").first.bounding_box()
    x0, y0 = min(t["x"], m["x"]) - PAD, t["y"] - PAD
    await pub.screenshot(path=out / name, clip={"x": x0, "y": y0, "width": max(t["x"] + t["width"], m["x"] + m["width"]) - x0 + PAD,
                                                "height": m["y"] + m["height"] - y0 + PAD})
    await pub.context.browser.close()


async def main(out):
    async with async_playwright() as p:
        page = await shots.backend_tab(p, width=1280, height=800)
        await _sorting.ready(page)
        mod = (await shots.rpc(page, "ir.module.module", "search", [[["name", "=", "vmk_language_sequence"]]]))[0]
        await shots.rpc(page, "ir.module.module", "button_immediate_uninstall", [[mod]]); await _sorting.ready(page)
        await selector(p, out, "selector_before.png")
        await shots.rpc(page, "ir.module.module", "button_immediate_install", [[mod]]); await _sorting.ready(page)
        for seq, code in enumerate(ORDER, 1):
            ids = await shots.rpc(page, "res.lang", "search", [[["code", "=", code]]])
            await shots.rpc(page, "res.lang", "write", [ids, {"sequence": seq}])
        await selector(p, out, "selector_after.png")
        await page.goto(shots.BASE + "/odoo/action-base.res_lang_act_window?debug=1", wait_until="networkidle")
        await page.wait_for_selector(".o_list_view .o_data_row"); await page.wait_for_timeout(800)
        await shots.polish(page, _sorting.HIDE); await shots.park_mouse(page, 1280, 800)
        # the enabled languages sort first; crop just below the last of them
        last = await page.locator(".o_list_view .o_data_row").nth(len(ORDER) - 1).bounding_box()
        await page.screenshot(path=out / "main_screenshot.png", clip={"x": 0, "y": 0, "width": 1280, "height": last["y"] + last["height"] + 1})
        await page.goto(shots.BASE + "/odoo?debug=", wait_until="networkidle")
    print("wrote", out)


if __name__ == "__main__":
    asyncio.run(main(shots.out_dir("vmk_language_sequence", sys.argv)))
