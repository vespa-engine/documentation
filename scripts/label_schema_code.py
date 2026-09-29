#!/usr/bin/env python3
"""Label schema code blocks in MDX pages as vespa-schema, so they are syntax highlighted.

Only the language of a fence is changed (```js expandable -> ```vespa-schema expandable);
which blocks are schema code is decided by is_schema() in jekyll_to_mdx.py.

Usage:
    scripts/label_schema_code.py                # all pages under en/ and ja/
    scripts/label_schema_code.py en/querying    # pages under a path
    scripts/label_schema_code.py --dry-run
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from jekyll_to_mdx import ROOT, SCHEMA_LANG, is_schema  # noqa: E402

OPEN_RE = re.compile(r"^([ \t]*)(`{3,}|~{3,})([^\s`]*)(.*)$")


def label(text: str, counts: Counter) -> str:
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        m = OPEN_RE.match(lines[i])
        if not m:
            i += 1
            continue
        indent, marker, lang, meta = m.groups()
        close = re.compile(rf"^[ \t]*{re.escape(marker[0])}{{{len(marker)},}}[ \t]*$")
        j = i + 1
        while j < len(lines) and not close.match(lines[j]):
            j += 1
        code = "\n".join(line[len(indent):] if line.startswith(indent) else line for line in lines[i + 1 : j])
        if lang != SCHEMA_LANG and is_schema(code):
            counts[lang or "(none)"] += 1
            lines[i] = f"{indent}{marker}{SCHEMA_LANG}{meta}"
        i = j + 1
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("paths", nargs="*", default=["en", "ja"], help="files or directories (default: en ja)")
    parser.add_argument("--dry-run", action="store_true", help="report without writing")
    args = parser.parse_args()
    counts: Counter = Counter()
    changed = 0
    for arg in args.paths:
        p = ROOT / arg
        for path in sorted(p.rglob("*.mdx")) if p.is_dir() else [p]:
            text = path.read_text(encoding="utf-8")
            new = label(text, counts)
            if new != text:
                changed += 1
                if not args.dry_run:
                    path.write_text(new, encoding="utf-8")
    print(f"{sum(counts.values())} code blocks in {changed} pages labelled {SCHEMA_LANG}, previously: "
          + ", ".join(f"{k} {v}" for k, v in counts.most_common()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
