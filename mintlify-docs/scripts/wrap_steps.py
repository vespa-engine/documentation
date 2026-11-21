#!/usr/bin/env python3
"""Wrap sequential numbered lists in Mintlify Steps/Step components."""

from __future__ import annotations

import re
from pathlib import Path

APPS_DIR = Path(__file__).resolve().parent.parent / "en" / "applications"
STEP_START = re.compile(r"^(\d+)\.\s+(.*)$")
HEADING = re.compile(r"^#{1,6}\s")
STRUCTURAL = re.compile(
    r"^</?(Steps|Step|Frame|Warning|Note|Accordion|AccordionGroup)\b"
)


def is_fence(line: str) -> bool:
    return line.strip().startswith("```")


def collect_numbered_block(lines: list[str], start: int) -> tuple[list[list[str]], int] | None:
    """Collect a sequential 1..n numbered list starting at `start`. Returns steps, end index."""
    if start >= len(lines):
        return None
    m = STEP_START.match(lines[start])
    if not m or m.group(1) != "1":
        return None

    steps: list[list[str]] = []
    current: list[str] = [m.group(2)]
    expected = 2
    i = start + 1
    in_fence = False

    while i < len(lines):
        line = lines[i]

        if is_fence(line):
            in_fence = not in_fence
            current.append(line)
            i += 1
            continue

        if in_fence:
            current.append(line)
            i += 1
            continue

        if HEADING.match(line) or STRUCTURAL.match(line):
            break

        sm = STEP_START.match(line)
        if sm:
            num = int(sm.group(1))
            if num == expected:
                steps.append(current)
                current = [sm.group(2)]
                expected += 1
                i += 1
                continue
            if num == 1 and expected > 2:
                # Nested sub-list restart — keep inside current step
                current.append(line)
                i += 1
                continue
            break

        # Continuation of current step (blank lines, indented text, code-adjacent prose)
        if line.strip() == "" or not STEP_START.match(line):
            current.append(line)
            i += 1
            continue

        break

    if len(current) > 0 or not steps:
        steps.append(current)

    if len(steps) < 2:
        return None

    return steps, i


def steps_to_mdx(steps: list[list[str]]) -> list[str]:
    out = ["<Steps>"]
    for step_lines in steps:
        out.append("  <Step>")
        body = "\n".join(step_lines).strip("\n")
        if body:
            for bl in body.split("\n"):
                out.append(f"  {bl}" if bl else "")
        out.append("  </Step>")
        out.append("")
    out.append("</Steps>")
    return out


def process_file(path: Path) -> bool:
    lines = path.read_text(encoding="utf-8").split("\n")
    out: list[str] = []
    i = 0
    in_frontmatter = False
    fm_done = 0
    changed = False

    while i < len(lines):
        line = lines[i]

        if i == 0 and line.strip() == "---":
            in_frontmatter = True
            fm_done = 1
        if in_frontmatter:
            out.append(line)
            if line.strip() == "---" and fm_done > 0 and i > 0:
                fm_done += 1
                if fm_done >= 2:
                    in_frontmatter = False
            i += 1
            continue

        if line.strip().startswith("<Steps>"):
            # Already wrapped — copy until </Steps>
            out.append(line)
            i += 1
            while i < len(lines) and lines[i].strip() != "</Steps>":
                out.append(lines[i])
                i += 1
            if i < len(lines):
                out.append(lines[i])
                i += 1
            continue

        block = collect_numbered_block(lines, i)
        if block:
            steps, end = block
            out.extend(steps_to_mdx(steps))
            out.append("")
            i = end
            changed = True
            continue

        out.append(line)
        i += 1

    if changed:
        text = "\n".join(out)
        text = re.sub(r"\n{3,}", "\n\n", text)
        path.write_text(text.rstrip() + "\n", encoding="utf-8")
    return changed


def main() -> None:
    for path in sorted(APPS_DIR.glob("*.mdx")):
        if process_file(path):
            print(f"Updated {path.name}")


if __name__ == "__main__":
    main()
