"""Shared helpers for store screenshots: a logged-in backend tab, a public page, and capture polish.

Every change made here is to the page in the browser, for the capture only; no module ships any of it.
See README.md for what the recipes expect to find in the database.
"""
import re

BASE = "http://localhost:8069"
MARK = "vmk-shots"  # window.name of the one backend tab the recipes reuse

# Screenshot-only polish, applied after a backend page loads:
# - hide the unread-messages counter;
# - repaint Odoo's Violet colour (index 11) in our purple, with core's subtle tint for the light parts;
# - paint the calendar sidebar's current-date circle in the popover header's pale violet;
# - repaint the signed-in user's letter avatar (Mitchell Admin, user 2, partner 3) in our purple.
POLISH = r"""async (extraCss) => {
  const style = document.createElement('style');
  style.textContent = `
    .o-mail-MessagingMenu-counter { display: none !important; }
    .o_calendar_color_11, .o_calendar_renderer .o_calendar_color_11 {
      --o-event-bg: #531B93 !important; --fc-event-bg-color: rgb(178,152,206) !important;
      --o-event-bg--subtle-rgb: 178,152,206 !important; }
    .o_field_color_picker .o_colorlist_item_color_11 { background-color: #531B93 !important; }
    .o_calendar_sidebar .o_date_item_cell.o_selected { background: radial-gradient(circle,
      rgb(241, 235, 252) 0% calc(100% / sqrt(2)), transparent calc(100% / sqrt(2)) 100%) !important; }
  ` + (extraCss || '');
  document.head.appendChild(style);
  const mine = /res[.]partner[/]3[/]avatar|res[.]users[/]2[/]avatar|model=res[.]users&field=avatar_128&id=2(?![0-9])/;
  for (const img of [...document.querySelectorAll('img')].filter(i => mine.test(i.getAttribute('src') || ''))) {
    let svg;
    try { svg = await (await fetch(img.src)).text(); } catch (e) { continue; }  // mid-reload: leave it
    if (!svg.trim().startsWith('<')) continue;
    img.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(
      svg.replace(/fill=['"](#?[0-9a-fA-F]{3,6}|hsl\([^)]*\)|rgb\([^)]*\))['"]/, "fill='#531B93'"));
  }
}"""

# A macOS-style arrow drawn into the page, since headless screenshots never include the real cursor.
CURSOR = r"""([x, y]) => {
  const c = document.createElement('div'); c.id = 'vmk-cursor';
  c.style.cssText = `position:fixed; left:${x}px; top:${y}px; z-index:100000; pointer-events:none;`;
  c.innerHTML = `<svg width="17" height="25" viewBox="0 0 17 25" xmlns="http://www.w3.org/2000/svg">
    <path d="M1.5 1.5 L1.5 19.5 L6 15.3 L9.2 22.6 L12 21.4 L8.9 14.3 L14.8 14.3 Z"
          fill="#000" stroke="#fff" stroke-width="1.5" stroke-linejoin="round"/></svg>`;
  document.body.appendChild(c);
}"""


async def backend_tab(p, width=1280, height=800, scale=2):
    """The one reusable tab in the debugging Chrome, logged in to the backend, at `scale`x."""
    browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    ctx = browser.contexts[0]
    for page in ctx.pages:
        try:
            if await page.evaluate("window.name") == MARK:
                break
        except Exception:
            pass
    else:
        page = await ctx.new_page()
        await page.goto(BASE + "/odoo")
        await page.evaluate(f"window.name = '{MARK}'")
    cdp = await ctx.new_cdp_session(page)  # the override lasts while this session does
    await cdp.send("Emulation.setDeviceMetricsOverride",
                   {"width": width, "height": height, "deviceScaleFactor": scale, "mobile": False})
    page._vmk_cdp = cdp
    return page


async def public_page(p, width=1280, height=800, scale=2):
    """A fresh headless page for the public website, logged out, in English (UK)."""
    browser = await p.chromium.launch()
    return await browser.new_page(viewport={"width": width, "height": height},
                                  device_scale_factor=scale, locale="en-GB")


async def polish(page, extra_css=""):
    await page.evaluate(POLISH, extra_css)
    await page.wait_for_timeout(300)


async def open_backend(page, path, wait=".o_form_view, .o_list_view, .o_calendar_view, .o_setting_container",
                       extra_css=""):
    await page.goto(BASE + path, wait_until="networkidle")
    await page.wait_for_selector(wait)
    await page.wait_for_timeout(800)
    await polish(page, extra_css)


async def park_mouse(page, width, height):
    await page.mouse.move(width - 5, height - 5)
    await page.wait_for_timeout(300)


def day_cell(page, day):
    """The calendar sidebar's cell for day-of-month `day`, matched exactly (9 must not match 29)."""
    return page.locator(".o_calendar_sidebar .o_date_item_cell").filter(has_text=re.compile(rf"^\s*{day}\s*$")).first


async def rpc(page, model, method, args, kwargs=None):
    """Call the ORM as the tab's logged-in user, to find demo records by name rather than by id.

    Always in English (UK), the screenshots' language, since demo names may be translated there."""
    kwargs = {**(kwargs or {}), "context": {"lang": "en_GB", **(kwargs or {}).get("context", {})}}
    return await page.evaluate("""async ([model, method, args, kwargs]) => {
        const r = await fetch(`/web/dataset/call_kw/${model}/${method}`, {method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({jsonrpc: '2.0', method: 'call', params: {model, method, args, kwargs}})});
        const j = await r.json(); if (j.error) throw new Error(j.error.data.message); return j.result; }""",
        [model, method, args, kwargs])


async def record_id(page, model, name):
    ids = await rpc(page, model, "search", [[["name", "=", name]]], {"limit": 1})
    if not ids:
        raise SystemExit(f"no {model} named {name!r}: see README.md for the demo data the recipes expect")
    return ids[0]


def out_dir(module, argv):
    """Where a recipe writes: the module's static/description, or --out DIR for a trial run."""
    from pathlib import Path
    if "--out" in argv:
        d = Path(argv[argv.index("--out") + 1]); d.mkdir(parents=True, exist_ok=True); return d
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import repos
    return repos.module_dir(module) / "static" / "description"
