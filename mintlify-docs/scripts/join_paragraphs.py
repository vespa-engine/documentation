#!/usr/bin/env python3
"""Join wrapped prose lines into single lines in MDX files."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def is_fence(line: str) -> bool:
    return line.strip().startswith("```")


def is_structural(line: str) -> bool:
    s = line.strip()
    if not s:
        return False
    if re.match(r"^#{1,6}\s", s):
        return True
    if re.match(
        r"^</?(Accordion|AccordionGroup|Warning|Note|Frame|Steps|Step|Card|Tabs|Tab|Info|Tip|Check|Callout|Danger)\b",
        s,
    ):
        return True
    if re.match(r"^</?(table|tbody|thead|tr|th|td|caption|dl|dt|dd)\b", s, re.I):
        return True
    if s == "---":
        return True
    if re.match(r"^(title|sidebarTitle|description):", s):
        return True
    if s.startswith("{/*") or s.endswith("*/}") or s == "*/}":
        return True
    if re.match(r"^\|", s):
        return True
    if re.match(r"^!\[", s):
        return True
    if s.startswith("{`") or (s.startswith("{") and "$$" in s):
        return True
    if re.match(r"^####\s", s):
        return True
    return False


def is_list_item(line: str) -> bool:
    return bool(re.match(r"^\s*[-*]\s+", line)) or bool(re.match(r"^\s*\d+\.\s+", line))


def join_lines(group: list[str]) -> str:
    return " ".join(l.strip() for l in group)


def join_p_block(lines: list[str]) -> str:
    """Join a multi-line <p>...</p> block into one line."""
    text = " ".join(l.strip() for l in lines)
    return re.sub(r"\s+", " ", text)


def process_block(block: list[str]) -> list[str]:
    result: list[str] = []
    i = 0
    while i < len(block):
        line = block[i]
        s = line.strip()
        if s.startswith("<p") and "</p>" not in s:
            group = [line]
            i += 1
            while i < len(block) and "</p>" not in block[i]:
                group.append(block[i])
                i += 1
            if i < len(block):
                group.append(block[i])
                i += 1
            result.append(join_p_block(group))
            continue
        if is_structural(line):
            result.append(line)
            i += 1
            continue
        if is_list_item(line):
            group = [line]
            i += 1
            while i < len(block) and not is_list_item(block[i]) and not is_structural(block[i]):
                if block[i].strip().startswith("<p"):
                    break
                group.append(block[i])
                i += 1
            result.append(join_lines(group))
            continue
        group = [line]
        i += 1
        while i < len(block) and not is_list_item(block[i]) and not is_structural(block[i]):
            if block[i].strip().startswith("<p"):
                break
            group.append(block[i])
            i += 1
        result.append(join_lines(group))
    return result


def process_file(path: Path) -> tuple[int, int]:
    lines = path.read_text(encoding="utf-8").split("\n")
    output: list[str] = []
    i = 0
    in_code = False
    in_frontmatter = False
    fm_count = 0

    while i < len(lines):
        line = lines[i]

        if i == 0 and line.strip() == "---":
            in_frontmatter = True
            fm_count = 1

        if in_frontmatter:
            output.append(line)
            if line.strip() == "---" and fm_count > 0 and i > 0:
                fm_count += 1
                if fm_count >= 2:
                    in_frontmatter = False
            i += 1
            continue

        if is_fence(line):
            in_code = not in_code
            output.append(line)
            i += 1
            continue
        if in_code:
            output.append(line)
            i += 1
            continue
        if not line.strip():
            output.append(line)
            i += 1
            continue

        block: list[str] = []
        while i < len(lines) and lines[i].strip() and not is_fence(lines[i]):
            block.append(lines[i])
            i += 1
        output.extend(process_block(block))

    before = len(lines)
    after = len(output)
    path.write_text("\n".join(output), encoding="utf-8")
    return before, after


def main() -> None:
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "en" / "reference" / "api"
    if target.is_file():
        paths = [target]
    else:
        paths = sorted(target.glob("*.mdx"))
    for path in paths:
        before, after = process_file(path)
        print(f"{path.name}: {before} -> {after} lines")


if __name__ == "__main__":
    main()
