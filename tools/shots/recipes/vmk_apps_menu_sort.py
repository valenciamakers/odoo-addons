# /// script
# requires-python = ">=3.11"
# dependencies = ["playwright>=1.50"]
# ///
"""Apps Menu Sort: the app grid before and after, full window and cropped to its icons.

Writes main_screenshot.png and the before and after crops into the module. Uninstalls it for the
"before" captures and installs it again; see _sorting.py.
"""
import asyncio, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _sorting

if __name__ == "__main__":
    asyncio.run(_sorting.run("vmk_apps_menu_sort", [_sorting.grid], sys.argv))
