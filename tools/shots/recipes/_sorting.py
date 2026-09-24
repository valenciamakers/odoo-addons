"""Shared captures for the three sort modules: each view before and after its module.

`run(module, views)` uninstalls the module over RPC, captures every view's crops as
`<part>_before.png`, installs it again, and captures them as `<part>_after.png`, plus the full
window as `main_screenshot.png`. Uninstalling one sort module leaves the
other two alone, so each "before" differs from its "after" in that module only.
"""
import asyncio, sys
from pathlib import Path
from playwright.async_api import async_playwright
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import shots

# capture-only: the trial database's expiry banner, and developer mode's bug icon and database name
HIDE = """
    .database_expiration_panel { display: none !important; }
    .o_menu_systray .o_debug_manager, .o_user_menu .oe_topbar_name { display: none !important; }"""
PAD = 16


async def grid(page, out, phase):
    """The app grid, cropped to its icons."""
    await page.goto(shots.BASE + "/odoo?debug=", wait_until="networkidle")
    await page.wait_for_selector(".o_home_menu .o_app"); await page.wait_for_timeout(1000)
    await shots.polish(page, HIDE); await shots.park_mouse(page, 1280, 800)
    if phase == "after":
        await page.screenshot(path=out / "main_screenshot.png")
    box = await page.evaluate("""(() => { const r = [...document.querySelectorAll('.o_home_menu .o_app')].map(e => e.getBoundingClientRect());
        return {x: Math.min(...r.map(b => b.left)), y: Math.min(...r.map(b => b.top)), r: Math.max(...r.map(b => b.right)), b: Math.max(...r.map(b => b.bottom))}; })()""")
    await page.screenshot(path=out / f"grid_{phase}.png", clip={
        "x": box["x"] - PAD, "y": box["y"] - PAD, "width": box["r"] - box["x"] + 2 * PAD, "height": box["b"] - box["y"] + 2 * PAD})


async def apps(page, out, phase):
    """The Apps page, filtered to installed apps, and its first rows of cards."""
    await shots.open_backend(page, "/odoo/apps?debug=", wait=".o_kanban_view", extra_css=HIDE)
    await page.click(".o_searchview_dropdown_toggler"); await page.wait_for_timeout(500)
    await page.locator(".o_filter_menu .o-dropdown-item, .o_filter_menu .dropdown-item", has_text="Installed").first.click()
    await page.wait_for_timeout(1200); await page.keyboard.press("Escape"); await page.wait_for_timeout(500)
    await shots.polish(page, HIDE); await shots.park_mouse(page, 1280, 800)
    if phase == "after":
        await page.screenshot(path=out / "main_screenshot.png")
    box = await page.locator(".o_kanban_renderer").bounding_box()
    await page.screenshot(path=out / f"apps_{phase}.png", clip={"x": box["x"], "y": box["y"], "width": box["width"], "height": 520})


async def settings(page, out, phase):
    """The Settings window with the Technical menu open, in developer mode, and the two lists alone."""
    await page.goto(shots.BASE + "/odoo/settings?debug=1", wait_until="networkidle")
    await page.wait_for_selector(".settings_tab"); await page.wait_for_timeout(800)
    await shots.polish(page, HIDE)
    side = await page.locator(".settings_tab").bounding_box()
    last = await page.locator(".settings_tab .tab").last.bounding_box()
    await page.screenshot(path=out / f"sidebar_{phase}.png", clip={
        "x": side["x"], "y": side["y"], "width": side["width"], "height": last["y"] + last["height"] - side["y"] + PAD})
    await page.locator(".o_menu_sections button, .o_menu_sections a", has_text="Technical").first.click(); await page.wait_for_timeout(800)
    await page.mouse.move(1275, 795)
    if phase == "after":
        await page.screenshot(path=out / "main_screenshot.png")
    menu = await page.locator(".o-dropdown--menu").first.bounding_box()
    await page.screenshot(path=out / f"technical_{phase}.png", clip={"x": menu["x"], "y": menu["y"], "width": menu["width"], "height": menu["height"]})
    await page.keyboard.press("Escape")


async def ready(page):
    """Wait until the backend serves again: an install or uninstall reloads the registry, and a
    request made meanwhile fails. Recipes run back to back hit the previous one's reload."""
    for _attempt in range(15):
        await page.wait_for_timeout(1500)
        try:
            await page.goto(shots.BASE + "/odoo", wait_until="networkidle")
            await page.wait_for_selector(".o_home_menu, .o_main_navbar", timeout=10000)
            await shots.rpc(page, "res.users", "search_count", [[]])
            return
        except Exception:
            continue
    raise SystemExit("the backend did not come back after the module was (un)installed")


async def run(module, views, argv):
    out = shots.out_dir(module, argv)
    async with async_playwright() as p:
        page = await shots.backend_tab(p, width=1280, height=800)
        await ready(page)
        mod = (await shots.rpc(page, "ir.module.module", "search", [[["name", "=", module]]]))[0]
        for phase, method in (("before", "button_immediate_uninstall"), ("after", "button_immediate_install")):
            await shots.rpc(page, "ir.module.module", method, [[mod]])
            await ready(page)
            for view in views:
                await view(page, out, phase)
        await page.goto(shots.BASE + "/odoo?debug=", wait_until="networkidle")
    print("wrote", out)
