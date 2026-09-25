"""Where a module and its store-asset sources live: this repo, or the private one beside it.

The tools are published here, but not every module they serve is. The Private repo's modules sit in
../Odoo Addons - Private, and their icon, cover, and screenshot sources in that repo's own tools/, in
the same layout as ours, since they describe modules we do not publish. Every lookup tries this repo
first, then that one, and a machine without the Private repo simply never finds it.

A cover in the Private repo takes the shared stylesheet from here, by relative path:
<link rel="stylesheet" href="../../../Odoo%20Addons%20-%20Custom/tools/covers/cover.css">
"""

from pathlib import Path

PUBLIC = Path(__file__).resolve().parent.parent
PRIVATE = PUBLIC.parent / "Odoo Addons - Private"
REPOS = [repo for repo in (PUBLIC, PRIVATE) if repo.is_dir()]


def module_dir(module):
    """The module's directory, in whichever repo holds it."""
    for repo in REPOS:
        if (repo / module / "__manifest__.py").exists():
            return repo / module
    raise SystemExit(f"{module} is not a module in {' or '.join(str(r) for r in REPOS)}")


def tools_dir(module):
    """The tools/ of the repo holding the module, where its sources belong."""
    return module_dir(module).parent / "tools"


def source(kind, name):
    """tools/<kind>/<name> from whichever repo has it, or None."""
    for repo in REPOS:
        path = repo / "tools" / kind / name
        if path.exists():
            return path
    return None


def sources(kind, pattern):
    """Every tools/<kind>/<pattern> across the repos."""
    return sorted(path for repo in REPOS for path in (repo / "tools" / kind).glob(pattern))


def shown(path):
    """A path relative to the directory both repos sit in, for messages."""
    return path.relative_to(PUBLIC.parent)
