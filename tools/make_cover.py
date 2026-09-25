# /// script
# requires-python = ">=3.11"
# dependencies = ["playwright>=1.50"]
# ///
"""Render a module's Apps Store cover, static/description/cover.png, from tools/covers/<module>.html.

A cover is the thumbnail the store shows in search results and at the top of the module's page. The
store fills a 2:1 frame with it, so each cover is laid out at 880x440 CSS px on the shared
tools/covers/cover.css and rendered at 2x, 1760x880. Covers reference the module's own screenshots
and icon by relative path, so re-rendering after a new screenshot picks it up.

    uv run tools/make_cover.py vmk_event_slot_multiday
    uv run tools/make_cover.py --all
    uv run tools/make_icon.py --install-browser     # once, if Playwright's Chromium is missing

The manifest's `images` list must name cover.png first: the store takes the first image as the
cover. Chromium is forced to sRGB so the purple comes out as #531B93 rather than the display's
profile.
"""

import argparse
import asyncio
import sys
from pathlib import Path

import repos


async def render(modules):
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(args=["--force-color-profile=srgb", "--allow-file-access-from-files"])
        except Exception:
            sys.exit("No Chromium for Playwright: run `uv run tools/make_icon.py --install-browser`")
        page = await browser.new_page(viewport={"width": 880, "height": 440}, device_scale_factor=2)
        for module in modules:
            await page.goto(repos.source("covers", f"{module}.html").as_uri(), wait_until="load")
            await page.evaluate("document.fonts.ready")
            out = repos.module_dir(module) / "static" / "description" / "cover.png"
            await page.screenshot(path=out, clip={"x": 0, "y": 0, "width": 880, "height": 440})
            print(f"rendered {repos.shown(out)}")
        await browser.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("module", nargs="?", help="technical name, e.g. vmk_event_slot_multiday")
    parser.add_argument("--all", action="store_true", help="re-render every module with a cover in tools/covers/")
    args = parser.parse_args()
    if args.all:
        modules = [p.stem for p in repos.sources("covers", "vmk_*.html")]
    elif args.module:
        if not repos.source("covers", f"{args.module}.html"):
            sys.exit(f"no tools/covers/{args.module}.html in either repo")
        modules = [args.module]
    else:
        parser.error("name a module, or pass --all")
    asyncio.run(render(modules))


if __name__ == "__main__":
    main()
