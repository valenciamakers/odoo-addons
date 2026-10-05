# /// script
# requires-python = ">=3.11"
# dependencies = ["polib"]
# ///
"""Keep each module's PO files in step with its POT, and say where they are not.

A POT is what `odoo i18n export` wrote; the PO files beside it are edited by hand, entry by entry,
as strings change. Nothing ties the two together, so a PO drifts: its `#:` reference lines keep
naming a view or a file the string has left, it keeps an entry the POT dropped, or it never gains
one the POT added. Odoo hides the first of these, since it merges each PO against its POT on load
and takes the POT's references, but a PO that says otherwise misleads whoever reads it next. It
does not hide the others: a PO entry missing from the POT is dropped in silence, and a POT entry
missing from a PO, or left blank in it, shows English.

Run on a module, this rewrites the `#.` and `#:` lines of every PO entry from the POT's, leaving
each msgid, msgstr, and translator comment exactly as written. It never adds, removes, or
translates an entry: those it reports, for a person to settle.

    uv run tools/i18n_sync.py vmk_event_host
    uv run tools/i18n_sync.py --all
    uv run tools/i18n_sync.py --all --check    # report only, exit 1 where anything is out of step
"""

import argparse
import sys
from pathlib import Path

import polib

sys.path.insert(0, str(Path(__file__).resolve().parent))
import repos  # noqa: E402

# A catalogue allowed to hold only the entries that differ from the English source.
PARTIAL = {"en_GB"}


def blocks(text):
    """The file as its header and one text block per entry, in file order."""
    return text.rstrip("\n").split("\n\n")


def generated(block):
    """The lines the exporter writes above an entry: `#.` comments and `#:` references."""
    return [line for line in block.split("\n") if line.startswith(("#.", "#:"))]


def keyed(path):
    """msgid -> its text block, for every entry of a catalogue."""
    parts = blocks(path.read_text())[1:]
    entries = [e for e in polib.pofile(str(path)) if not e.obsolete]
    if len(parts) != len(entries):
        raise SystemExit(f"{repos.shown(path)}: {len(parts)} blocks but {len(entries)} entries; fix by hand")
    return {(e.msgctxt, e.msgid): (block, e) for block, e in zip(parts, entries)}


def sync(module, check):
    """Bring one module's PO files in step with its POT. Returns the problems left for a person."""
    i18n = repos.module_dir(module) / "i18n"
    pot_path = i18n / f"{module}.pot"
    if not pot_path.exists():
        return [f"{module}: no POT"]
    pot = keyed(pot_path)
    problems = []
    for po_path in sorted(i18n.glob("*.po")):
        name = f"{module} {po_path.stem}"
        po = keyed(po_path)
        for key in pot.keys() - po.keys():
            if po_path.stem not in PARTIAL:
                problems.append(f"{name}: missing {key[1][:70]!r}")
        for key in po.keys() - pot.keys():
            problems.append(f"{name}: not in the POT, so never loaded: {key[1][:70]!r}")
        text = po_path.read_text()
        stale = 0
        for key, (block, entry) in po.items():
            if key not in pot:
                continue
            if not entry.msgstr and not entry.msgstr_plural:
                problems.append(f"{name}: blank {key[1][:70]!r}")
            if "fuzzy" in entry.flags:
                problems.append(f"{name}: fuzzy {key[1][:70]!r}")
            wanted = generated(pot[key][0])
            if generated(block) == wanted:
                continue
            stale += 1
            kept = [line for line in block.split("\n") if not line.startswith(("#.", "#:"))]
            # Translator comments (`# `) lead, then the exporter's lines, then flags and strings.
            lead = [line for line in kept if line.startswith("#") and not line.startswith("#,")]
            rest = [line for line in kept if line not in lead]
            text = text.replace(block, "\n".join(lead + wanted + rest), 1)
        if stale and check:
            problems.append(f"{name}: {stale} entries whose references differ from the POT's")
        elif stale:
            po_path.write_text(text)
            print(f"{name}: references of {stale} entries taken from the POT")
    return problems


def modules():
    return sorted(p.parent.parent.name for repo in repos.REPOS for p in repo.glob("*/i18n/*.pot"))


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("module", nargs="*", help="technical names, e.g. vmk_event_host")
    parser.add_argument("--all", action="store_true", help="every module with a POT, in both repos")
    parser.add_argument("--check", action="store_true", help="change nothing; exit 1 if anything is out of step")
    args = parser.parse_args()
    names = modules() if args.all else args.module
    if not names:
        parser.error("name a module, or pass --all")
    problems = [problem for name in names for problem in sync(name, args.check)]
    for problem in problems:
        print(problem)
    if not problems:
        print(f"{len(names)} modules in step with their POT")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
