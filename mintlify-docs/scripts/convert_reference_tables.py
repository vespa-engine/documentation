#!/usr/bin/env python3
"""Convert HTML tables to markdown in all en/reference MDX files."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mdx_html_tables import convert_tree  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent / "en" / "reference"


SKIP = {"query.mdx"}


def main() -> None:
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT
    count = 0
    for path in sorted(target.rglob("*.mdx")):
        if path.name in SKIP:
            continue
        from mdx_html_tables import convert_mdx_file

        if convert_mdx_file(path):
            print(f"Converted tables in {path.name}")
            count += 1
    print(f"Updated {count} files")


if __name__ == "__main__":
    main()
