# /// script
# requires-python = ">=3.11"
# dependencies = ["playwright>=1.50", "pillow>=11"]
# ///
"""Render a module's store icon, static/description/icon.png, from an SVG glyph.

Each module's glyph lives in tools/icons/<module>.svg: a Lucide icon copied as published, or our own
drawing on Lucide's 24px grid. The icon is a 256px rounded tile in our purple with the glyph in
white, rendered at its final size so nothing is resampled.

    uv run tools/make_icon.py vmk_event_slot_multiday          # render from tools/icons/
    uv run tools/make_icon.py vmk_foo --lucide calendar-range   # fetch a Lucide glyph first
    uv run tools/make_icon.py --all                             # re-render every module
    uv run tools/make_icon.py --install-browser                 # once: Playwright's Chromium

Chromium draws the shapes, black on a white tile; Pillow then paints the colours, using the tile's
alpha and the glyph's inverted luminance as masks. Screenshots pass through the browser's colour
management, which shifted #531B93 to #4C1F8D when the colours were drawn in the page, so the page
never draws them.
"""

import argparse
import asyncio
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
ICONS = Path(__file__).resolve().parent / "icons"
LUCIDE = "https://cdn.jsdelivr.net/npm/lucide-static@1.47.0/icons/{}.svg"

SIZE = 256  # the tile
GLYPH = 160  # the glyph's 24px box; Lucide leaves ~2px of it empty on each side
RADIUS = 0.2  # of SIZE
PURPLE = (0x53, 0x1B, 0x93, 255)
WHITE = (255, 255, 255, 255)

PAGE = """<!doctype html><html><head><style>
html, body {{ margin: 0; background: transparent; }}
#tile {{ width: {size}px; height: {size}px; border-radius: {radius}px; background: #fff; color: #000;
         display: flex; align-items: center; justify-content: center; }}
#tile svg {{ width: {glyph}px; height: {glyph}px; }}
</style></head><body><div id="tile">{svg}</div></body></html>"""


def fetch_lucide(module, name):
    dest = ICONS / f"{module}.svg"
    dest.write_bytes(urllib.request.urlopen(LUCIDE.format(name), timeout=30).read())
    print(f"fetched lucide {name} -> {dest.relative_to(ROOT)}")


async def render(modules):
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch()
        except Exception:
            sys.exit("No Chromium for Playwright: run `uv run tools/make_icon.py --install-browser`")
        page = await browser.new_page(viewport={"width": SIZE, "height": SIZE}, device_scale_factor=1)
        for module in modules:
            svg = (ICONS / f"{module}.svg").read_text()
            await page.set_content(PAGE.format(size=SIZE, radius=int(SIZE * RADIUS), glyph=GLYPH, svg=svg))
            with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
                await page.locator("#tile").screenshot(path=tmp.name, omit_background=True)
                shot = Image.open(tmp.name).convert("RGBA")
            glyph = ImageOps.invert(shot.convert("L"))
            icon = Image.composite(Image.new("RGBA", shot.size, WHITE), Image.new("RGBA", shot.size, PURPLE), glyph)
            icon.putalpha(shot.getchannel("A"))
            out = ROOT / module / "static" / "description" / "icon.png"
            icon.save(out, optimize=True)
            print(f"rendered {out.relative_to(ROOT)}")
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
        modules = sorted(p.stem for p in ICONS.glob("*.svg"))
    elif args.module:
        if not (ROOT / args.module / "__manifest__.py").exists():
            sys.exit(f"{args.module} is not a module in {ROOT}")
        if args.lucide:
            fetch_lucide(args.module, args.lucide)
        modules = [args.module]
    else:
        parser.error("name a module, or pass --all")
    asyncio.run(render(modules))


if __name__ == "__main__":
    main()
