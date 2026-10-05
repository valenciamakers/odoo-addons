# /// script
# requires-python = ">=3.11"
# dependencies = ["polib"]
# ///
"""Write each module's catalogues for the secondary languages, from core's wording and our own.

Spanish and Catalan are written by hand and required of every module. The languages in
i18n_sync.SECONDARY are shipped as a courtesy, and this tool writes them whole: every
`i18n/<lang>.po` for those languages is its output, never edited in place. For each string of a
module's POT it takes the first of:

1. tools/i18n/overrides.json, `{"<lang>": {"<msgid>": {"msgstr": "...", "why": "..."}}}`: a
   wording we chose over the one this tool would copy from core, with the reason beside it.
   Nearly all are a short English string core uses in another sense: a slot machine, a login
   session, a mail recipient.
2. Core's own translation of the same English, in this series: read from every catalogue of the
   Odoo source checkouts, preferring the Events modules', then base, web, and mail, then whichever
   wording most modules use.
3. An email body core translates, with our inserted lines put back at the same places: a
   `mail.template` body of ours that is core's body plus whole lines.
4. The translation already in the file, or in another of our modules for the same English.
5. A JSON file given with --memory, `{"<msgid>": "<msgstr>"}`, named `<lang>.json`: how newly
   written translations enter.

A string with none of those stays blank and shows English, and the run says how many each language
lacks. Strings our Spanish leaves as the English (a product name, a bare placeholder) are copied.

    uv run tools/i18n_fill.py vmk_event_host
    uv run tools/i18n_fill.py --all
    uv run tools/i18n_fill.py --all --memory /path/to/dir    # dir holds fr.json, de.json, ...
    uv run tools/i18n_fill.py --all --todo /path/to/dir      # write what each language still lacks

Core is found in odoo-community-<series> and odoo-enterprise-<series> under ../Data Sources, or in
the directories named by --core (repeatable): each one a directory of addons.
"""

import argparse
import difflib
import json
import re
import sys
from collections import defaultdict
from multiprocessing import Pool
from pathlib import Path

import polib

sys.path.insert(0, str(Path(__file__).resolve().parent))
import repos  # noqa: E402
from i18n_sync import PRIMARY, SECONDARY  # noqa: E402

HERE = Path(__file__).resolve().parent
SERIES = re.search(r"\((\d+\.\d+)\)", repos.PUBLIC.name)
PREFERRED = ["event", "website_event", "event_sale", "base", "web", "mail", "website", "calendar", "base_setup"]
STRING = re.compile(r'"((?:[^"\\]|\\.)*)"')
ESCAPE = re.compile(r"\\(.)")
TAG = re.compile(r"<[^>]+>")
SPLIT = re.compile(r"(<[^>]+>)")
UNCLOSED = re.compile(r"""(<[a-z]+\b[^<>]*["'])([^<>"'=]+)(</[a-z]+>)""")
PLACEHOLDER = re.compile(r"%\([a-z_]+\)[sd]|%[sd]|\{\{.*?\}\}")


def unquote(part):
    return ESCAPE.sub(lambda m: {"n": "\n", "t": "\t"}.get(m.group(1), m.group(1)), "".join(STRING.findall(part)))


def read_core(job):
    """One core catalogue: its translations of the strings we want, and its email bodies.

    A hand parser, since polib takes minutes over a language's eight hundred catalogues.
    """
    path, lang, module, wanted = job
    found, bodies = {}, []
    for block in Path(path).read_text(encoding="utf-8").split("\n\n")[1:]:
        if "#~" in block or "#, fuzzy" in block or "msgid " not in block or "\nmsgstr" not in block:
            continue
        source, _, target = block[block.index("msgid ") :].partition("\nmsgstr")
        msgid, msgstr = unquote(source[6:]), unquote(target.split("\nmsgstr[1]")[0])
        if not msgstr:
            continue
        if msgid in wanted:
            found[msgid] = msgstr
        elif ",body_html:" in block:
            bodies.append((msgid, msgstr))
    return lang, module, found, bodies


def core_dirs(given):
    if given:
        return [Path(p) for p in given]
    if not SERIES:
        return []
    sources = repos.PUBLIC.parent / "Data Sources"
    community = sources / f"odoo-community-{SERIES[1]}"
    return [p for p in (community / "odoo/addons", community / "addons", sources / f"odoo-enterprise-{SERIES[1]}") if p.is_dir()]


def load_core(dirs, wanted):
    """lang -> msgid -> core's wording, and lang -> [(body msgid, body msgstr)]."""
    jobs = [
        (str(po), lang, po.parent.parent.name, wanted)
        for root in dirs
        for lang in SECONDARY
        for po in root.glob(f"*/i18n/{lang}.po")
    ]
    said = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    bodies = defaultdict(list)
    with Pool() as pool:
        for lang, module, found, found_bodies in pool.imap_unordered(read_core, jobs, chunksize=32):
            for msgid, msgstr in found.items():
                said[lang][msgid][msgstr].append(module)
            bodies[lang] += found_bodies

    def rank(item):
        modules = item[1]
        return (min((PREFERRED.index(m) for m in modules if m in PREFERRED), default=99), -len(modules), item[0])

    return {lang: {m: min(v.items(), key=rank)[0] for m, v in d.items()} for lang, d in said.items()}, bodies


def with_our_lines(ours, core_source, core_translation):
    """Core's translated body with the lines we inserted into its source, or None if it will not fit.

    Line for line where the translation kept the source's lines, as most do. Where a translator
    joined or split lines, each block of ours goes in before the same tag it precedes in the source.
    """
    core_translation = mended(core_source, core_translation)
    if core_translation is None:
        return None
    source, wanted, translated = core_source.split("\n"), ours.split("\n"), core_translation.split("\n")
    inserts = []  # (source line our block goes in before, the block)
    for op, i1, _i2, j1, j2 in difflib.SequenceMatcher(None, source, wanted, autojunk=False).get_opcodes():
        if op == "insert":
            inserts.append((i1, wanted[j1:j2]))
        elif op != "equal":
            return None
    if len(source) == len(translated):
        for at, block in reversed(inserts):
            translated[at:at] = block
        result = "\n".join(translated)
    else:
        tokens = SPLIT.split(core_translation)
        tags = [n for n, token in enumerate(tokens) if token.startswith("<") and not token.startswith("<!--")]
        for at, block in reversed(inserts):
            before = len(markup("\n".join(source[:at])))  # how many tags precede our block in the source
            if before >= len(tags):
                return None
            gap = tags[before] - 1  # the text between the tag before our block and the one after
            head, newline, tail = tokens[gap].rpartition("\n")
            if tail.strip() or (not newline and head.strip()):
                return None  # words sit where our block belongs: not ours to split
            tokens[gap] = head + "\n" + "\n".join(block) + "\n" + tail
        result = "".join(tokens)
    return result if markup(result) == markup(ours) else None


def mended(source, translation):
    """A core translation with its markup made whole, or None where that is more than a closing tag.

    Core ships email bodies a translator broke: a closing tag dropped, so that the rest of the email
    sits inside a link. Each missing closing tag goes back where the source has it, after the words
    it closes. Anything else that differs is refused, and the email stays English in that language.
    """
    if markup(source) == markup(translation):
        return translation
    # An opening tag that lost its `>`, so its words run on from the last attribute:
    # `<strong t-out="x"oggi</strong>`.
    translation = UNCLOSED.sub(r"\1>\2\3", translation)
    tokens = SPLIT.split(translation)
    tags = [n for n, token in enumerate(tokens) if token.startswith("<") and not token.startswith("<!--")]
    wanted, found = markup(source), markup(translation)
    for op, i1, i2, j1, _j2 in reversed(difflib.SequenceMatcher(None, wanted, found, autojunk=False).get_opcodes()):
        if op == "equal":
            continue
        missing = wanted[i1:i2]
        if op != "delete" or not all(tag.startswith("</") for tag in missing) or not 0 < j1 < len(tags):
            return None
        text = tokens[tags[j1] - 1]  # the words before the tag that follows the gap
        words = text.rstrip()
        tokens[tags[j1] - 1] = words + "".join(missing) + text[len(words) :]
    result = "".join(tokens)
    return result if markup(result) == wanted else None


def markup(text):
    """A body's tags, without comments or the texts inside a tag a translator may translate.

    Those are an `alt` or `title`, and the fallback in a QWeb expression: `object.name or 'Guest'`.
    Anything else that differs is a broken translation, and core ships some: see mended().
    """
    tags = (re.sub(r'(alt|title)="[^"]*"', r'\1=""', t) for t in TAG.findall(text) if not t.startswith("<!--"))
    return [re.sub(r"or '[^']*'", "or ''", t) for t in tags]


def sound(msgid, msgstr):
    """Whether a translation keeps the source's placeholders, line breaks, and markup.

    Core's own catalogues fail this now and then: a translator who renders a CSS class along with
    the text leaves an icon that never draws.
    """
    return (
        sorted(PLACEHOLDER.findall(msgid)) == sorted(PLACEHOLDER.findall(msgstr))
        # An email body is HTML, where a translator may join lines freely; a message is not.
        and (len(msgid) > 1000 or msgid.count("\n") == msgstr.count("\n"))
        and sorted(markup(msgid)) == sorted(markup(msgstr))
    )


def header(pot, lang, plural):
    metadata = dict(pot.metadata)
    metadata.update({"Language": lang, "Plural-Forms": plural, "Last-Translator": "", "Language-Team": ""})
    return metadata


def fill(module, core, bodies, ours, memory, overrides, plurals, todo):
    i18n = repos.module_dir(module) / "i18n"
    pot = polib.pofile(str(i18n / f"{module}.pot"))
    spanish = {e.msgid: e.msgstr for e in polib.pofile(str(i18n / "es.po"))} if (i18n / "es.po").exists() else {}
    lacking = {}
    for lang in SECONDARY:
        path = i18n / f"{lang}.po"
        existing = {e.msgid: e.msgstr for e in polib.pofile(str(path))} if path.exists() else {}
        po = polib.POFile(wrapwidth=78)
        po.header = (
            f"Translation of Odoo Server.\nThis file contains the translation of the following modules:\n"
            f"\t* {module}\n\nWritten by tools/i18n_fill.py: do not edit by hand. Core's wording where core\n"
            f"has the same English, ours otherwise. See DEVELOPING.md.\n"
        )
        po.metadata = header(pot, lang, plurals.get(lang, ""))
        blank = 0
        for entry in pot:
            msgid = entry.msgid
            msgstr = overrides.get(lang, {}).get(msgid) or core.get(lang, {}).get(msgid)
            if not msgstr and len(msgid) > 1000:
                for source, translation in bodies.get(lang, ()):
                    msgstr = with_our_lines(msgid, source, translation)
                    if msgstr:
                        break
            msgstr = msgstr or existing.get(msgid) or ours.get(lang, {}).get(msgid) or memory.get(lang, {}).get(msgid)
            if not msgstr and spanish.get(msgid) == msgid:
                msgstr = msgid
            if msgstr and not sound(msgid, msgstr):
                print(f"{module} {lang}: placeholders or line breaks differ, left blank: {msgid[:60]!r}")
                msgstr = ""
            if not msgstr:
                blank += 1
                todo[lang][msgid].add(module)
            po.append(
                polib.POEntry(
                    msgid=msgid,
                    msgstr=msgstr or "",
                    comment=entry.comment,
                    occurrences=entry.occurrences,
                    flags=entry.flags,
                )
            )
        po.save(str(path))
        if blank:
            lacking[lang] = blank
    return lacking


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("module", nargs="*", help="technical names, e.g. vmk_event_host")
    parser.add_argument("--all", action="store_true", help="every module with a POT, in both repos")
    parser.add_argument("--core", action="append", help="a directory of core addons; repeatable")
    parser.add_argument("--memory", help="a directory of <lang>.json files of new translations")
    parser.add_argument("--todo", help="a directory to write <lang>.json into: the strings each language lacks")
    args = parser.parse_args()
    every = sorted(p.parent.parent.name for repo in repos.REPOS for p in repo.glob("*/i18n/*.pot"))
    names = every if args.all else args.module
    if not names:
        parser.error("name a module, or pass --all")
    dirs = core_dirs(args.core)
    if not dirs:
        raise SystemExit("no core addons found; pass --core <directory of addons>")

    wanted = {e.msgid for m in every for e in polib.pofile(str(repos.module_dir(m) / "i18n" / f"{m}.pot"))}
    core, bodies = load_core(dirs, wanted)
    plurals = {}
    for lang in SECONDARY:
        for root in dirs:
            base = root / "base" / "i18n" / f"{lang}.po"
            if base.exists():
                plurals[lang] = polib.pofile(str(base)).metadata.get("Plural-Forms", "")
    # The same English in another of our modules takes the same translation.
    ours = defaultdict(dict)
    for m in every:
        for lang in SECONDARY:
            path = repos.module_dir(m) / "i18n" / f"{lang}.po"
            if path.exists():
                ours[lang].update({e.msgid: e.msgstr for e in polib.pofile(str(path)) if e.msgstr})
    memory = {}
    if args.memory:
        memory = {p.stem: json.loads(p.read_text()) for p in Path(args.memory).glob("*.json")}
    overrides_path = HERE / "i18n" / "overrides.json"
    overrides = {}
    if overrides_path.exists():
        overrides = {
            lang: {msgid: chosen["msgstr"] for msgid, chosen in strings.items()}
            for lang, strings in json.loads(overrides_path.read_text()).items()
        }

    todo = defaultdict(lambda: defaultdict(set))
    for name in names:
        lacking = fill(name, core, bodies, ours, memory, overrides, plurals, todo)
        summary = ", ".join(f"{lang} {n}" for lang, n in lacking.items()) or "complete"
        print(f"{name}: {len(SECONDARY)} languages; blank: {summary}")
    if args.todo:
        out = Path(args.todo)
        out.mkdir(parents=True, exist_ok=True)
        for lang, strings in todo.items():
            (out / f"{lang}.json").write_text(
                json.dumps({m: sorted(mods) for m, mods in sorted(strings.items())}, ensure_ascii=False, indent=1)
            )
    assert not set(SECONDARY) & set(PRIMARY)


if __name__ == "__main__":
    main()
