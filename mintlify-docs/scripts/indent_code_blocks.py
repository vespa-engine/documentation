#!/usr/bin/env python3
"""Indent content inside fenced code blocks in MDX files."""

from __future__ import annotations

import re
from pathlib import Path

APPS_DIR = Path(__file__).resolve().parent.parent / "en" / "applications"
PAD = "    "


def looks_like_xml(code: str) -> bool:
    s = code.strip()
    return s.startswith("<") or "<services" in s or "<container" in s or "<chain" in s


def looks_like_java(code: str) -> bool:
    return (
        "import " in code
        or "public class" in code
        or "public void" in code
        or "@Override" in code
        or "extends " in code
    )


def indent_xml(code: str) -> str:
    lines = code.split("\n")
    out: list[str] = []
    level = 0
    stack: list[str] = []
    for raw in lines:
        s = raw.strip()
        if not s:
            out.append("")
            continue
        if s.startswith("<?") or s.startswith("<!--"):
            out.append(s)
            continue
        if s in ("...", "…"):
            out.append(PAD * level + s)
            continue
        if s.startswith("</"):
            tag = re.match(r"</(\w+)", s)
            if tag and stack and stack[-1] == tag.group(1):
                stack.pop()
                level = max(0, level - 1)
            elif level > 0:
                level -= 1
            out.append(PAD * level + s)
            continue
        if s.endswith("/>") or re.match(r"<[^>]+>.*</[^>]+>$", s):
            out.append(PAD * level + s)
            continue
        if s.startswith("<"):
            tag = re.match(r"<(\w+)", s)
            out.append(PAD * level + s)
            if tag and not s.endswith("/>") and "</" not in s[1:]:
                stack.append(tag.group(1))
                level += 1
            continue
        out.append(PAD * level + s)
    return "\n".join(out)


def indent_java(code: str) -> str:
    """Basic Java brace-based indentation for flattened blocks."""
    if "\n" in code and code.count("\n") > 3:
        # Already multiline — normalize brace indent only
        lines = code.split("\n")
    else:
        # Single line or few lines — split on common tokens
        s = code.strip()
        if "{" not in s and ";" not in s:
            return code
        # Split after ; and { } for readability
        s = re.sub(r"\s*;\s*", ";\n", s)
        s = re.sub(r"\s*\{\s*", " {\n", s)
        s = re.sub(r"\s*\}\s*", "\n}\n", s)
        lines = [ln.strip() for ln in s.split("\n") if ln.strip()]

    out: list[str] = []
    level = 0
    for line in lines:
        s = line.strip()
        if not s:
            continue
        if s.startswith("}"):
            level = max(0, level - 1)
        out.append(PAD * level + s)
        if s.endswith("{") and not s.startswith("}"):
            level += 1
    return "\n".join(out)


def indent_shell(code: str) -> str:
    lines = code.split("\n")
    out = []
    for line in lines:
        s = line.strip()
        if not s:
            out.append("")
            continue
        if s.endswith("\\"):
            out.append(s)
        elif s.startswith("-D") or s.startswith("$"):
            out.append(s)
        else:
            out.append(s)
    return "\n".join(out)


def indent_block(code: str, lang: str) -> str:
    lang = (lang or "").lower()
    if lang in ("xml", "txt", "yaml", "yml") and looks_like_xml(code):
        return indent_xml(code)
    if lang in ("java",) or looks_like_java(code):
        return indent_java(code)
    if lang in ("bash", "shell", "sh") and code.strip().startswith("$"):
        return indent_shell(code)
    if looks_like_xml(code):
        return indent_xml(code)
    return code


def process_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    parts = re.split(r"(^```[\w-]*\n)(.*?)(^```\s*$)", text, flags=re.MULTILINE | re.DOTALL)
    if len(parts) < 2:
        return False

    changed = False
    new_parts = [parts[0]]
    i = 1
    while i < len(parts):
        if i + 2 < len(parts) and parts[i].startswith("```"):
            fence_open = parts[i]
            body = parts[i + 1]
            fence_close = parts[i + 2]
            lang_match = re.match(r"^```([\w-]*)", fence_open)
            lang = lang_match.group(1) if lang_match else ""
            new_body = indent_block(body.rstrip("\n"), lang)
            if new_body != body.rstrip("\n"):
                changed = True
            new_parts.append(fence_open)
            new_parts.append(new_body + "\n")
            new_parts.append(fence_close)
            i += 3
        else:
            new_parts.append(parts[i])
            i += 1

    if changed:
        path.write_text("".join(new_parts), encoding="utf-8")
    return changed


def main() -> None:
    for path in sorted(APPS_DIR.glob("*.mdx")):
        if process_file(path):
            print(f"Updated {path.name}")


if __name__ == "__main__":
    main()
