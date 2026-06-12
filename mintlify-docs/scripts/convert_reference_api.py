#!/usr/bin/env python3
"""Convert en/reference/api/*.html to Mintlify MDX."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from html_to_mdx import convert_file  # noqa: E402
from fix_mdx_parse_errors import (  # noqa: E402
    escape_mdx_curly_in_math,
    fix_frontmatter,
    generic_pre_to_fences,
    jekyll_highlight_to_fences,
    jekyll_note_to_mdx,
)

API_DIR = Path(__file__).resolve().parent.parent / "en" / "reference" / "api"


def post_fix(path: Path) -> bool:
    original = path.read_text(encoding="utf-8")
    text = fix_frontmatter(original)
    text = jekyll_note_to_mdx(text)
    text = jekyll_highlight_to_fences(text)
    text = generic_pre_to_fences(text)
    text = escape_mdx_curly_in_math(text)
    if text != original:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def main() -> None:
    for path in sorted(API_DIR.glob("*.html")):
        convert_file(path)
    for path in sorted(API_DIR.glob("*.mdx")):
        if post_fix(path):
            print(f"Post-fixed {path.name}")


if __name__ == "__main__":
    main()
