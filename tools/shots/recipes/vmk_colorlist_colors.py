# /// script
# requires-python = ">=3.11"
# dependencies = ["playwright>=1.50"]
# ///
"""Custom Colors: the Colors list opened from Settings, the setting itself, and a contact's tags
with the color picker open on one of them.

Writes main_screenshot.png, settings.png, and tag_picker.png. Expects the demo's three custom
colors (Slate, Brown, Emphasis) and its contact tags (README.md).
"""
import asyncio, sys
from pathlib import Path
from playwright.async_api import async_playwright
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import shots

CONTACT = "Rosa Vidal"
# capture-only: the polish repaints Violet (11) in our purple for every capture, which here would
# misstate it, so it is painted Odoo's own Violet again (models/palette.py)
VIOLET = ".o_colorlist_item_color_11 { background-color: #9872e6 !important; }"
# capture-only: a swatch names its color in a native `title`, which a headless screenshot never
# shows, so the name is drawn beside it as a tooltip, in the look of Odoo's own (the list's undo
# arrow), to its left, where it hides no other swatch
TOOLTIP = r"""(el) => {
  const r = el.getBoundingClientRect(), tip = document.createElement('div');
  tip.id = 'vmk-tooltip'; tip.textContent = el.title;
  tip.style.cssText = `position:fixed; z-index:99999; left:${r.left - 12}px; top:${r.top + r.height / 2}px;
    transform:translate(-100%, -50%); background:#000; color:#fff; font-size:13px; line-height:1.5;
    padding:4px 8px; border-radius:6px; white-space:nowrap; box-shadow:0 2px 6px rgba(0,0,0,.2);`;
  document.body.appendChild(tip);
}"""


async def main(out):
    async with async_playwright() as p:
        page = await shots.backend_tab(p)
        await shots.goto(page, shots.BASE + "/odoo")
        contact = await shots.record_id(page, "res.partner", CONTACT)
        # the setting, in General Settings
        await shots.open_backend(page, "/odoo/settings", extra_css=VIOLET)
        block = page.locator("#vmk_colorlist_colors")
        await block.scroll_into_view_if_needed(); await page.wait_for_timeout(500)
        await shots.park_mouse(page, 1280, 800)
        box = await block.bounding_box()
        await page.screenshot(path=out / "settings.png",
                              clip={"x": box["x"], "y": box["y"], "width": 520, "height": box["height"]})  # to the help's end
        # the list, from the setting's button, with the pointer on Emphasis' undo arrow; in a window
        # 960px wide, where its three columns sit close enough to read across
        await page.set_viewport_size({"width": 960, "height": 760})
        await page.locator("#vmk_colorlist_colors button", has_text="Edit Colors").click()
        await page.wait_for_selector(".o_list_view .o_data_row")
        await page.wait_for_timeout(800)
        await shots.polish(page, VIOLET)
        row = page.locator(".o_data_row", has_text="Emphasis")
        undo = row.locator("button[name=action_reset]:not(.disabled)")
        ubox = await undo.bounding_box()
        x, y = ubox["x"] + ubox["width"] / 2, ubox["y"] + ubox["height"] / 2
        await page.mouse.move(x, y, steps=6); await page.wait_for_timeout(1200)  # the tooltip
        await page.evaluate(shots.CURSOR, [x - 1, y - 1])
        table = await page.locator(".o_list_table").bounding_box()
        await page.screenshot(path=out / "main_screenshot.png",
                              clip={"x": 0, "y": 0, "width": 960, "height": table["y"] + table["height"] + 24})
        await page.evaluate("document.getElementById('vmk-cursor')?.remove()")
        await page.set_viewport_size({"width": 1280, "height": 800})
        # a contact's tags, the picker open on Member, the pointer on Emphasis' swatch
        await shots.open_backend(page, f"/odoo/contacts/{contact}", extra_css=VIOLET)
        tag = page.locator("div[name=category_id] .o_tag", has_text="Member").first
        await tag.click()
        picker = page.locator(".o_colorlist_popover, .o_popover .o_colorlist").first
        await picker.wait_for()
        swatch = picker.locator("[title=Emphasis]").first
        sbox = await swatch.bounding_box()
        x, y = sbox["x"] + sbox["width"] * 0.6, sbox["y"] + sbox["height"] * 0.65
        await page.mouse.move(x, y, steps=6); await page.wait_for_timeout(1200)
        await swatch.evaluate(TOOLTIP)
        await page.evaluate(shots.CURSOR, [x - 1, y - 1])
        tags = await tag.bounding_box()
        pbox = await page.locator(".o_popover:has(.o_colorlist)").last.bounding_box()  # with its checkbox
        tip = await page.locator("#vmk-tooltip").bounding_box()
        left = min(tags["x"], pbox["x"], tip["x"]) - 24
        top = tags["y"] - 16
        right = max(tags["x"] + 360, pbox["x"] + pbox["width"], tip["x"] + tip["width"]) + 24
        bottom = pbox["y"] + pbox["height"] + 24
        await page.screenshot(path=out / "tag_picker.png",
                              clip={"x": left, "y": top, "width": right - left, "height": bottom - top})
    return out


if __name__ == "__main__":
    out = shots.out_dir("vmk_colorlist_colors", sys.argv)
    asyncio.run(main(out)); print("wrote", out)
