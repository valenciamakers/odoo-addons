# /// script
# requires-python = ">=3.11"
# dependencies = ["playwright>=1.50", "pillow>=11"]
# ///
"""Render a module's store icon, static/description/icon.png, from an SVG glyph.

Each module's glyph lives in tools/icons/<module>.svg: a Lucide icon copied as published, or our own
drawing on Lucide's 24px grid. The icon is the glyph alone, in our purple on a transparent
background, filling a 256px square and rendered at its final size so nothing is resampled. The Apps
Store frames an icon in its own white box, and Odoo's own app icons have no tile either.

    uv run tools/make_icon.py vmk_event_slot_multiday          # render from tools/icons/
    uv run tools/make_icon.py vmk_foo --lucide calendar-range   # fetch a Lucide glyph first
    uv run tools/make_icon.py --all                             # re-render every module
    uv run tools/make_icon.py --install-browser                 # once: Playwright's Chromium

Chromium draws the glyph black on white; Pillow then paints it purple and takes its alpha from the
render's inverted luminance. Drawing on white rather than on transparency is what lets a composition
knock a gap out of a glyph with a white shape: white becomes transparent, as the background does.
Screenshots pass through the browser's colour management, which shifted #531B93 to #4C1F8D when the
colours were drawn in the page, so the page never draws them.
"""

import argparse
import asyncio
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

from PIL import Image, ImageOps

import repos
LUCIDE = "https://cdn.jsdelivr.net/npm/lucide-static@1.47.0/icons/{}.svg"

SIZE = 256  # the icon, and the glyph's 24px box; Lucide leaves ~2px of the box empty on each side
PURPLE = (0x53, 0x1B, 0x93, 255)

PAGE = """<!doctype html><html><head><style>
html, body {{ margin: 0; background: transparent; }}
#tile {{ width: {size}px; height: {size}px; background: #fff; color: #000; }}
#tile svg {{ display: block; width: {size}px; height: {size}px; }}
</style></head><body><div id="tile">{svg}</div></body></html>"""


def fetch_lucide(module, name):
    dest = repos.tools_dir(module) / "icons" / f"{module}.svg"
    dest.write_bytes(urllib.request.urlopen(LUCIDE.format(name), timeout=30).read())
    print(f"fetched lucide {name} -> {repos.shown(dest)}")


async def render(modules):
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch()
        except Exception:
            sys.exit("No Chromium for Playwright: run `uv run tools/make_icon.py --install-browser`")
        page = await browser.new_page(viewport={"width": SIZE, "height": SIZE}, device_scale_factor=1)
        for module in modules:
            svg = repos.source("icons", f"{module}.svg").read_text()
            await page.set_content(PAGE.format(size=SIZE, svg=svg))
            with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
                await page.locator("#tile").screenshot(path=tmp.name)
                shot = Image.open(tmp.name)
            icon = Image.new("RGBA", shot.size, PURPLE)
            icon.putalpha(ImageOps.invert(shot.convert("L")))
            out = repos.module_dir(module) / "static" / "description" / "icon.png"
            icon.save(out, optimize=True)
            print(f"rendered {repos.shown(out)}")
        await browser.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("module", nargs="?", help="technical name, e.g. vmk_event_slot_multiday")
    parser.add_argument("--lucide", metavar="NAME", help="fetch this Lucide icon as the module's glyph first")
    parser.add_argument("--all", action="store_true", help="re-render every module with a glyph in tools/icons/")
    parser.add_argument("--install-browser", action="store_true", help="download Playwright's Chromium")
    args = parser.parse_args()

    if args.install_browser:
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
        return
    if args.all:
        modules = [p.stem for p in repos.sources("icons", "*.svg")]
    elif args.module:
        repos.module_dir(args.module)  # exits if no repo holds it
        if args.lucide:
            fetch_lucide(args.module, args.lucide)
        modules = [args.module]
    else:
        parser.error("name a module, or pass --all")
    asyncio.run(render(modules))


if __name__ == "__main__":
    main()
