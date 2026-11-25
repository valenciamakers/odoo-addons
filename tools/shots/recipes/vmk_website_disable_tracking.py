# /// script
# requires-python = ">=3.11"
# dependencies = ["playwright>=1.50"]
# ///
"""Disable Visitor Tracking: the Track Visitors setting in the Website settings.

Writes main_screenshot.png. Expects tracking off on the demo's website, as the module leaves it on
install.
"""
import asyncio, sys
from pathlib import Path
from playwright.async_api import async_playwright
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import shots


async def main(out):
    async with async_playwright() as p:
        page = await shots.backend_tab(p)
        # the setting, with the pointer on its checkbox, from its block's title, Tracking & SEO, down
        # to the cookies bar beside it
        await shots.open_backend(page, "/odoo/action-website.action_website_configuration")
        setting = page.locator("#vmk_track_visitors_setting")
        await setting.evaluate("el => el.scrollIntoView({block: 'end'})"); await page.wait_for_timeout(500)
        title = await setting.evaluate("""el => { const r = el.closest('.o_settings_container')
            .previousElementSibling.getBoundingClientRect(); return [r.left, r.top, r.width]; }""")
        left, top, width = title
        row = await setting.bounding_box()
        cookies = await page.locator("#website_cookies_bar_setting").bounding_box()
        bottom = max(row["y"] + row["height"], cookies["y"] + cookies["height"]) + 24
        check = await setting.locator("input[type=checkbox]").bounding_box()
        x, y = check["x"] + check["width"] * 0.6, check["y"] + check["height"] * 0.7
        await page.mouse.move(x, y, steps=6); await page.wait_for_timeout(400)
        await page.evaluate(shots.CURSOR, [x - 1, y - 1])
        await page.screenshot(path=out / "main_screenshot.png",
                              clip={"x": left, "y": top, "width": width, "height": bottom - top})
    return out


if __name__ == "__main__":
    out = shots.out_dir("vmk_website_disable_tracking", sys.argv)
    asyncio.run(main(out)); print("wrote", out)
