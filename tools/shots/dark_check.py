# /// script
# requires-python = ">=3.11"
# dependencies = ["playwright>=1.50"]
# ///
"""Render a module's page in the backend's Apps menu, in Enterprise's dark or light mode.

Emulates the system colour scheme in the reused backend tab; Enterprise's colour-scheme service
follows it on 19; 18 follows only its cookie, which is set too. The tab is left light.

    uv run tools/shots/dark_check.py vmk_event_host /tmp/dark.png dark
"""
import asyncio, sys
from pathlib import Path
from playwright.async_api import async_playwright
sys.path.insert(0, str(Path(__file__).resolve().parent))
import shots


async def main(module, out, scheme):
    async with async_playwright() as p:
        page = await shots.backend_tab(p, width=1280, height=900, scale=1)
        await page.emulate_media(color_scheme=scheme)
        await shots.color_scheme(page, scheme)  # 18 follows only the cookie
        await shots.goto(page, shots.BASE + "/odoo"); await page.wait_for_timeout(1500)
        mod = (await shots.rpc(page, "ir.module.module", "search", [[["name", "=", module]]]))[0]
        url = f"{shots.BASE}/odoo/action-base.open_module_tree/{mod}"
        await shots.goto(page, url); await page.wait_for_selector(".oe_styling_v8")
        h = await page.evaluate("document.querySelector('.o_form_sheet').scrollHeight + 200")
        await page._vmk_cdp.send("Emulation.setDeviceMetricsOverride",
                                 {"width": 1280, "height": int(h), "deviceScaleFactor": 1, "mobile": False})
        await page.wait_for_timeout(1500)
        await page.locator(".o_form_sheet").screenshot(path=out)
        await page.emulate_media(color_scheme="light")
        await shots.color_scheme(page, "light")  # leave the tab light for the next capture


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "dark")); print("wrote", sys.argv[2])
