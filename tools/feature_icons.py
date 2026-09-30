# /// script
# requires-python = ">=3.11"
# ///
"""Swap a module's store-page Font Awesome icons for Lucide ones, as files beside the page.

Each `<span class="fa fa-NAME fa-2x fa-fw">` in static/description/index.html becomes an
`<img src="icons/<icon>.svg">` at the same size, and the icon is written to
static/description/icons/: Lucide's SVG, pinned at the version make_icon.py uses, or, where the
mapping says `material:<name>`, a Material Symbols glyph, for an icon that must match Odoo's own.
Where it says `fa:<name>`, the Font Awesome span stays, for an icon that must match a series whose
backend still draws Font Awesome, in the same fixed colour as the other icons.
Each SVG fixes its colour at #9B69F4, which reads on white and on the dark theme alike; an image
cannot follow the page's colour scheme (see DEVELOPING.md). The licence of every family used ships
beside the icons, and icon files the page no longer names are removed.

Which icon replaces which is tools/icons/feature_icons.json: a default per Font Awesome glyph, and
per-module overrides where a sentence needs another. The page's remaining dark-mode purple,
#B794F4 before 30 September 2026, becomes #9B69F4 in the same pass.

    uv run tools/feature_icons.py vmk_event_host
    uv run tools/feature_icons.py --all
    uv run tools/feature_icons.py --check      # list pages still carrying Font Awesome, change nothing
"""

import argparse
import json
import re
import shutil
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import repos  # noqa: E402

LUCIDE = "https://cdn.jsdelivr.net/npm/lucide-static@1.47.0/icons/{}.svg"
MATERIAL = "https://fonts.gstatic.com/s/i/short-term/release/materialsymbolsoutlined/{}/default/24px.svg"
COLOR = "#9B69F4"
STYLE = f"<style>:root{{color:{COLOR}}}</style>"
SPAN = re.compile(r'<span class="fa fa-([a-z0-9-]+) fa-2x fa-fw" style="[^"]*"></span>')
FA_SPAN = '<span class="fa fa-{} fa-2x fa-fw" style="color:#9B69F4; margin-right:16px;"></span>'
IMG = '<img src="icons/{}.svg" alt="" width="28" height="28" style="width:28px; max-width:28px; margin-right:16px;"/>'
LICENSES = {"lucide": "LICENSE-lucide", "material": "LICENSE-material-symbols"}
MAPPING = json.loads((Path(__file__).resolve().parent / "icons" / "feature_icons.json").read_text())


def icon_for(module, fa):
    name = MAPPING["modules"].get(module, {}).get(fa) or MAPPING["default"].get(fa)
    if not name:
        raise SystemExit(f"{module}: no icon mapped for fa-{fa}; add it to tools/icons/feature_icons.json")
    return name


def fetch(url):
    return urllib.request.urlopen(url, timeout=30).read().decode()


def lucide_svg(name):
    svg = re.sub(r'\s*class="[^"]*"', "", fetch(LUCIDE.format(name)))
    return re.sub(r"(<svg[^>]*>)", r"\1\n  " + STYLE, svg, count=1)


def material_svg(name):
    svg = fetch(MATERIAL.format(name)).replace("<svg ", '<svg fill="currentColor" ', 1)
    svg = re.sub(r"(<svg[^>]*>)", r"\1" + STYLE, svg, count=1)
    return f"<!-- Material Symbols (Outlined) {name}, Apache-2.0: the glyph Odoo 20 itself draws -->\n{svg}\n"


def convert(module):
    desc = repos.module_dir(module) / "static" / "description"
    page = desc / "index.html"
    html = page.read_text()
    html = SPAN.sub(lambda m: replacement(icon_for(module, m.group(1))), html)
    html = re.sub("#B794F4", COLOR, html, flags=re.I)
    page.write_text(html)

    used = sorted(set(re.findall(r'src="icons/([a-z0-9-]+)\.svg"', html)))
    icons = desc / "icons"
    if not used:
        if icons.exists():
            shutil.rmtree(icons)
        return used
    icons.mkdir(exist_ok=True)
    families = set()
    for file in used:
        name = source_of(module, file)
        if name.startswith("material:"):
            families.add("material")
            (icons / f"{file}.svg").write_text(material_svg(name.split(":", 1)[1]))
        else:
            families.add("lucide")
            (icons / f"{file}.svg").write_text(lucide_svg(name))
    for stale in icons.glob("*.svg"):
        if stale.stem not in used:
            stale.unlink()
    for family, licence in LICENSES.items():
        target = icons / licence
        if family in families:
            shutil.copyfile(Path(__file__).resolve().parent / "icons" / licence, target)
        elif target.exists():
            target.unlink()
    return used


def replacement(name):
    if name.startswith("fa:"):
        return FA_SPAN.format(name.split(":", 1)[1])
    return IMG.format(file_of(name))


def file_of(name):
    """The file an icon is saved as: its own name, a Material one prefixed so the families never clash."""
    return name.replace("material:", "material-", 1)


def source_of(module, file):
    """The mapping entry a file came from, for every icon the page names."""
    entries = {icon for icon in MAPPING["default"].values()}
    entries |= {icon for icons in MAPPING["modules"].values() for icon in icons.values()}
    for entry in entries:
        if file_of(entry) == file:
            return entry
    return file  # a Lucide icon placed on the page by hand


def pages():
    return sorted({p.parent.parent.parent.name for repo in repos.REPOS
                   for p in repo.glob("vmk_*/static/description/index.html")})


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("module", nargs="?", help="technical name, e.g. vmk_event_host")
    parser.add_argument("--all", action="store_true", help="every module with a store page, in both repos")
    parser.add_argument("--check", action="store_true", help="list pages still using Font Awesome; change nothing")
    args = parser.parse_args()
    if args.check:
        left = {m: [fa for fa in SPAN.findall((repos.module_dir(m) / "static/description/index.html").read_text())
                    if not icon_for(m, fa).startswith("fa:")] for m in pages()}
        left = {m: fa for m, fa in left.items() if fa}
        for m, fa in left.items():
            print(f"{m}: {len(fa)} Font Awesome icons ({', '.join(sorted(set(fa)))})")
        print("none left" if not left else f"{len(left)} pages to convert")
        return
    targets = pages() if args.all else [args.module] if args.module else parser.error("give a module or --all")
    for module in targets:
        used = convert(module)
        print(f"{module}: {len(used)} icons ({', '.join(used)})")


if __name__ == "__main__":
    main()
