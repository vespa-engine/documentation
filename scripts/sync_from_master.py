#!/usr/bin/env python3
"""Bring the MDX pages up to date with changes to the Jekyll sources on master.

For each en/ page changed between BASE (the master commit of the previous sync) and REF,
master's changes are merged into the branch's page with a three-way merge:

    base   = jekyll_to_mdx.py output for the page at BASE
    ours   = the page on this branch
    theirs = jekyll_to_mdx.py output for the page at REF

so edits made on the branch are kept wherever master did not change the same lines. Where
both changed, master's version wins, and the branch's version of that part is reported.
New pages are converted, deleted pages are reported (not removed). Then code blocks get
the language master labels the same code with, since a change of language alone does not
show in the merge (both conversions use the current converter). Only master's own labels
are copied, not the converter's guesses for unlabeled code, which would override
languages set on the branch.

Navigation, images and redirects are not handled here: see _data/sidebar.yml on master,
assets/, and scripts/port_redirects.py.

Usage:
    scripts/sync_from_master.py BASE                 # merge master's changes since BASE
    scripts/sync_from_master.py BASE --dry-run       # report only
    scripts/sync_from_master.py BASE --ref origin/master
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import jekyll_to_mdx as J  # noqa: E402

ROOT = J.ROOT
FENCE_RE = re.compile(r"^([ \t]*)(`{3,}|~{3,})([^\s`]*)(.*)$")
COMPONENTS = r"<(Steps|Step|Card|CardGroup|Accordion|AccordionGroup|Tabs|Tab|Tip|Info|Columns|Tooltip|Frame)\b"


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout


def convert_all(ref: str, sources: list[str], guess: bool = True) -> dict[str, str | None]:
    J.REF = ref
    for f in (J.ref_file, J.ref_listing, J.site_variables, J.sidebar_names, J.redirects):
        f.cache_clear()
    guess_lang = J.guess_lang
    if not guess:
        J.guess_lang = lambda code: "txt"  # what copy_languages ignores; "" would make the meta the language
    try:
        out = {}
        for src in sources:
            text = J.ref_file(src)
            out[src] = None if text is None or "redirect_to:" in text[:600] else J.convert(text, src)
        return out
    finally:
        J.guess_lang = guess_lang


def merge(ours: str, base: str, theirs: str) -> tuple[str, list[str]]:
    """Three-way merge; conflicting parts take theirs. Returns the result and our side of each conflict."""
    with tempfile.TemporaryDirectory() as d:
        o, b, t = (Path(d) / n for n in ("ours", "base", "theirs"))
        o.write_text(ours, encoding="utf-8")
        b.write_text(base, encoding="utf-8")
        t.write_text(theirs, encoding="utf-8")
        args = ["git", "merge-file", "-p", "-L", "branch", "-L", "base", "-L", "master"]
        r = subprocess.run(args + [str(o), str(b), str(t)], capture_output=True, text=True)
        if r.returncode == 0:
            return r.stdout, []
        replaced = re.findall(r"^<<<<<<< branch\n(.*?)^=======", r.stdout, re.M | re.S)
        resolved = subprocess.run(args + ["--theirs", str(o), str(b), str(t)], capture_output=True, text=True).stdout
        return resolved, replaced


def code_blocks(text: str):
    """(line index of the opening fence, indent, marker, language, rest of the info string, normalized code)"""
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        m = FENCE_RE.match(lines[i])
        if not m:
            i += 1
            continue
        indent, marker, lang, meta = m.groups()
        close = re.compile(rf"^[ \t]*{re.escape(marker[0])}{{{len(marker)},}}[ \t]*$")
        j = i + 1
        while j < len(lines) and not close.match(lines[j]):
            j += 1
        code = "\n".join(line.strip() for line in lines[i + 1 : j] if line.strip())
        yield i, indent, marker, lang, meta, code
        i = j + 1


def copy_languages(page: str, master: str, counts: Counter) -> str:
    """Give each code block the language of the block with the same code in master's version,
    converted without guessing languages for unlabeled code."""
    langs: dict[str, str] = {}
    for _, _, _, lang, _, code in code_blocks(master):
        if lang and lang != "txt":
            langs.setdefault(code, lang)
    lines = page.split("\n")
    for i, indent, marker, lang, meta, code in list(code_blocks(page)):
        new = langs.get(code)
        if new and new != lang:
            counts[f"{lang or '(none)'} -> {new}"] += 1
            lines[i] = f"{indent}{marker}{new}{meta}"
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("base", help="master commit the branch was last synced with")
    parser.add_argument("--ref", default="origin/master", help="master commit to sync with (default: origin/master)")
    parser.add_argument("--dry-run", action="store_true", help="report without writing")
    args = parser.parse_args()

    changes = [line.split("\t") for line in git("diff", "--name-status", "-M", args.base, args.ref, "--", "en").splitlines()]
    changes = [(c[0][0], c[1], c[-1]) for c in changes if re.search(r"\.(html|md)$", c[-1])]
    sources = sorted({c[2] for c in changes if c[0] != "D"} | {c[1] for c in changes if c[0] in "MR"})
    base = convert_all(args.base, sources)
    theirs = convert_all(args.ref, sources)
    labelled = convert_all(args.ref, sources, guess=False)

    stats: Counter = Counter()
    langs: Counter = Counter()
    replaced: dict[str, list[str]] = {}
    for status, old_src, src in changes:
        target = ROOT / re.sub(r"\.(html|md)$", ".mdx", src)
        rel = target.relative_to(ROOT)
        if status == "D" or (status == "R" and old_src != src):
            old_target = ROOT / re.sub(r"\.(html|md)$", ".mdx", old_src)
            if old_target.exists():
                print(f"removed on master, still here: {old_target.relative_to(ROOT)}")
            if status == "D":
                continue
        if theirs.get(src) is None:
            stats["skipped (redirect stub)"] += 1
            continue
        if not target.exists():
            result = theirs[src]
            stats["new page"] += 1
            print(f"new page: {rel}")
        else:
            ours = target.read_text(encoding="utf-8")
            old = base.get(old_src) or base.get(src) or ""
            result, conflicts = merge(ours, J.keep_frontmatter(old, ours, ["description"]),
                                      J.keep_frontmatter(theirs[src], ours, ["description"]))
            if conflicts:
                replaced[str(rel)] = conflicts
            stats["conflicts, master wins" if conflicts else ("unchanged" if result == ours else "merged")] += 1
        result = copy_languages(result, labelled[src], langs)
        if not args.dry_run and (not target.exists() or result != target.read_text(encoding="utf-8")):
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(result, encoding="utf-8")

    print(f"{len(changes)} changed sources: " + ", ".join(f"{v} {k}" for k, v in stats.most_common()))
    if langs:
        print("code languages from master: " + ", ".join(f"{v} {k}" for k, v in langs.most_common()))
    if replaced:
        print(f"{len(replaced)} pages where master replaced branch edits (conflicts):")
        for page, parts in sorted(replaced.items()):
            comps = Counter(c for part in parts for c in re.findall(COMPONENTS, part))
            note = f"  [replaced components: {', '.join(f'{k} x{v}' for k, v in comps.items())}]" if comps else ""
            print(f"  {page}: {len(parts)}{note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
