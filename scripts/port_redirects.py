#!/usr/bin/env python3
"""Add the Jekyll redirects from master to the redirects in docs.json.

Sources are redirects.yml and the redirect_from lists in the page frontmatter on the
git ref (redirects.yml is generated from the latter, but can be out of date). Paths are
converted to Mintlify form (/en/foo.html -> /en/foo), chains are resolved, including
through the redirects already in docs.json, and destinations must be pages on this
branch. A redirect is not added when its source is an existing page, which it would
shadow, or when docs.json already has a redirect for that source.

Usage:
    scripts/port_redirects.py            # update docs.json
    scripts/port_redirects.py --dry-run  # only report
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import jekyll_to_mdx as J  # noqa: E402

ROOT = J.ROOT


def is_page(path: str) -> bool:
    p = path.strip("/")
    return (ROOT / f"{p}.mdx").is_file() or (ROOT / p / "index.mdx").is_file()


def jekyll_redirects() -> dict[str, str]:
    """Old path -> new path, both in Mintlify form."""
    pairs: dict[str, str] = {}
    for line in (J.ref_file("redirects.yml") or "").splitlines():
        m = re.match(r"\s*([^#\s]\S*):\s*(\S+)\s*$", line)
        if m:
            pairs[J.page_path(m.group(1))] = J.page_path(m.group(2))
    grep = subprocess.run(
        ["git", "grep", "-z", "-l", "^redirect_from:", J.REF, "--", "en"], cwd=ROOT, capture_output=True, text=True
    ).stdout
    for name in grep.split("\0"):
        source = name.partition(":")[2]
        if not re.search(r"\.(html|md)$", source):
            continue
        meta, _ = J.split_frontmatter(J.ref_file(source) or "")
        for old in meta.get("redirect_from") or []:
            old = str(old).strip().strip("\"'")
            if old:
                pairs.setdefault(J.page_path("/" + old.lstrip("/")), J.page_path("/" + source))
    return pairs


def resolve(path: str, *maps: dict[str, str]) -> str:
    seen = {path}
    while True:
        nxt = next((m[path] for m in maps if path in m), None)
        if nxt is None or nxt in seen:
            return path
        seen.add(nxt)
        path = nxt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--ref", default=J.REF, help=f"git ref holding the Jekyll sources (default: {J.REF})")
    parser.add_argument("--dry-run", action="store_true", help="report without writing docs.json")
    args = parser.parse_args()
    J.REF = args.ref

    docs_path = ROOT / "docs.json"
    text = docs_path.read_text(encoding="utf-8")
    docs = json.loads(text)
    existing = {r["source"]: r["destination"] for r in docs.get("redirects", [])}
    pairs = jekyll_redirects()

    added, skipped = [], {"source is a page": [], "already in docs.json": [], "destination is not a page": [], "self": []}
    for src in sorted(pairs):
        dst = resolve(src, existing, pairs)
        if src == dst:
            skipped["self"].append(src)
        elif is_page(src):
            skipped["source is a page"].append(f"{src} -> {dst}")
        elif src in existing:
            skipped["already in docs.json"].append(src)
        elif not is_page(dst):
            skipped["destination is not a page"].append(f"{src} -> {dst}")
        else:
            added.append({"source": src, "destination": dst})

    print(f"{len(pairs)} Jekyll redirects: {len(added)} added")
    for reason, items in skipped.items():
        if items:
            print(f"  skipped, {reason}: {len(items)}")
            for item in items:
                print(f"    {item}")
    if not args.dry_run and added:
        docs["redirects"] = docs.get("redirects", []) + added
        # keep the file's formatting: 2-space indent, no trailing newline if it had none
        out = json.dumps(docs, indent=2, ensure_ascii=False)
        docs_path.write_text(out + ("\n" if text.endswith("\n") else ""), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
