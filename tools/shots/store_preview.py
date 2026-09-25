# /// script
# requires-python = ">=3.11"
# dependencies = ["playwright>=1.50"]
# ///
"""Preview a module's store page inside the live Apps Store, before pushing it.

Loads a published module page on apps.odoo.com, swaps its description for our index.html with the
images embedded, and strips every inline style property the store drops, so what renders is what
the store will show. Kept: colour, font, margin, padding, border, width/max-width, display,
line-height, text-align, opacity (seen on published pages, September 2026).

    uv run tools/shots/store_preview.py vmk_event_host /tmp/preview.png
"""
import asyncio, base64, sys
from pathlib import Path
from playwright.async_api import async_playwright

HOST_PAGE = "https://apps.odoo.com/apps/modules/19.0/vmk_event_slot_multiday"
KEEP = ["color", "font-family", "font-size", "font-weight", "line-height", "text-align", "opacity", "display",
        "width", "max-width", "margin", "margin-left", "margin-right", "margin-top", "margin-bottom",
        "padding", "padding-left", "padding-right", "padding-top", "padding-bottom", "border"]
JS = """([html, keep, imgs]) => {
  const host = document.querySelector('.oe_styling_v8'); host.innerHTML = html;
  host.querySelectorAll('[style]').forEach(e => { const kept = [...e.style].filter(p => keep.includes(p))
    .map(p => p + ':' + e.style.getPropertyValue(p)); e.setAttribute('style', kept.join(';')); });
  host.querySelectorAll('img').forEach(i => { const d = imgs[i.getAttribute('src')]; if (d) i.src = d; });
}"""


async def main(module, out):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import repos
    desc = repos.module_dir(module) / "static" / "description"
    imgs = {f.name: "data:image/png;base64," + base64.b64encode(f.read_bytes()).decode() for f in desc.glob("*.png")}
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1280, "height": 900})
        await page.goto(HOST_PAGE, wait_until="networkidle")
        await page.evaluate(JS, [(desc / "index.html").read_text(), KEEP, imgs])
        await page.wait_for_timeout(800)
        await page.locator(".oe_styling_v8").screenshot(path=out)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1], sys.argv[2])); print("wrote", sys.argv[2])
