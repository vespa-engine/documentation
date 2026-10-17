#!/usr/bin/env python3
"""Fix common MDX parse errors in Vespa docs (Jekyll/HTML leftovers)."""

from __future__ import annotations

import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "en"


def fix_frontmatter(text: str) -> str:
    if not text.startswith("---"):
        return text
    end = text.find("\n---", 3)
    if end == -1:
        return text
    meta, body = text[3:end], text[end + 4 :]

    def quote_desc(m: re.Match) -> str:
        val = m.group(1).strip()
        if (val.startswith('"') and val.endswith('"')) or (
            val.startswith("'") and val.endswith("'")
        ):
            return m.group(0)
        escaped = val.replace("\\", "\\\\").replace('"', '\\"')
        return f'description: "{escaped}"'

    meta = re.sub(r"^description:\s*(.+)$", quote_desc, meta, flags=re.M)
    return f"---{meta}\n---{body}"


def jekyll_note_to_mdx(text: str) -> str:
    def note_repl(m: re.Match) -> str:
        content = html.unescape(m.group(2)).strip()
        return f"\n<Note>\n**Note:**\n\n{content}\n</Note>\n"

    def important_repl(m: re.Match) -> str:
        content = html.unescape(m.group(2)).strip()
        return f"\n<Warning>\n**Important:**\n\n{content}\n</Warning>\n"

    def pre_req_repl(m: re.Match) -> str:
        memory = m.group(1)
        extra = m.group(2) or ""
        extra = re.sub(r"<li>", "\n- ", extra)
        extra = re.sub(r"</li>", "", extra)
        extra = re.sub(r"<code>([^<]+)</code>", r"`\1`", extra)
        return (
            f"\n<Note>\n**Prerequisites:**\n\n"
            f"Memory: {memory}.{extra.strip()}\n</Note>\n"
        )

    text = re.sub(
        r"\{%\s*include\s+note\.html\s+content=(['\"])(.*?)\1\s*%\}",
        note_repl,
        text,
        flags=re.DOTALL,
    )
    text = re.sub(
        r"\{%\s*include\s+important\.html\s+content=(['\"])(.*?)\1\s*%\}",
        important_repl,
        text,
        flags=re.DOTALL,
    )
    text = re.sub(
        r"\{%\s*include\s+pre-req\.html\s+memory=(['\"])([^'\"]+)\1(?:\s+extra-reqs=(['\"])(.*?)\3)?\s*%\}",
        pre_req_repl,
        text,
        flags=re.DOTALL,
    )
    text = re.sub(r"\{%\s*include\s+video-include\.html[^%]*%\}", "", text, flags=re.DOTALL)
    text = re.sub(
        r"\{%\s*include\s+warning\.html\s+content=(['\"])(.*?)\1\s*%\}",
        important_repl,
        text,
        flags=re.DOTALL,
    )
    text = re.sub(
        r"\{%\s*include\s+setup\.html\s+appname=['\"]([^'\"]+)['\"]\s*%\}",
        lambda m: "",
        text,
    )
    text = re.sub(
        r"\{%\s*include\s+version\.html\s+version=[\"']([^\"']+)[\"']\s*%\}",
        lambda m: f"Vespa {m.group(1)}+",
        text,
    )
    return text


def html_comments_to_mdx(text: str) -> str:
    def repl(m: re.Match) -> str:
        content = m.group(1).strip()
        return f"{{/* {content} */}}"
    return re.sub(r"<!--(.*?)-->", repl, text, flags=re.DOTALL)


def pre_parent_to_fences(text: str) -> str:
    pattern = re.compile(
        r'<div class="pre-parent">\s*<button[^>]*></button>\s*'
        r"<pre(?:\s[^>]*)?>(.*?)</pre>\s*</div>",
        re.DOTALL | re.IGNORECASE,
    )

    def to_fence(m: re.Match) -> str:
        code = html.unescape(m.group(1)).strip()
        code = re.sub(r"<[^>]+>", "", code)
        lang = "bash" if code.startswith("$") else "txt"
        return f"\n```{lang}\n{code}\n```\n"

    return pattern.sub(to_fence, text)


def jekyll_highlight_to_fences(text: str) -> str:
    def pre_highlight(m: re.Match) -> str:
        lang = m.group(1) or "txt"
        code = html.unescape(m.group(2)).strip("\n")
        return f"\n```{lang}\n{code}\n```\n"

    text = re.sub(
        r"<pre>\s*\{%\s*highlight\s+(\w*)\s*%\}\s*(.*?)\s*\{%\s*endhighlight\s*%\}\s*</pre>",
        pre_highlight,
        text,
        flags=re.DOTALL,
    )
    text = re.sub(
        r"\{%\s*highlight\s+(\w*)\s*%\}\s*(.*?)\s*\{%\s*endhighlight\s*%\}",
        pre_highlight,
        text,
        flags=re.DOTALL,
    )
    return text


def escape_mdx_curly_in_math(text: str) -> str:
    """Escape { in $$ math blocks so MDX does not parse as JSX."""

    def fix_math(m: re.Match) -> str:
        inner = m.group(1)
        inner = inner.replace("{", "\\{").replace("}", "\\}")
        return f"$$ {inner} $$"

    return re.sub(r"\$\$\s*(.*?)\s*\$\$", fix_math, text, flags=re.DOTALL)


def fix_angle_in_tables(text: str) -> str:
    """Fix |<| table cells that break MDX."""
    lines = []
    for line in text.split("\n"):
        if "|" in line and re.search(r"\|[<>≤≥]\|", line):
            line = line.replace("|<|", "|`<`|").replace("|>|", "|`>`|")
            line = line.replace("|≤|", "|`≤`|").replace("|≥|", "|`≥`|")
        lines.append(line)
    return "\n".join(lines)


def generic_pre_to_fences(text: str) -> str:
    pattern = re.compile(r"<pre(?:\s[^>]*)?>(.*?)</pre>", re.DOTALL | re.IGNORECASE)

    def to_fence(m: re.Match) -> str:
        code = html.unescape(m.group(1)).strip()
        # Only unwrap Jekyll/HTML wrappers; do not strip API placeholders like <namespace>.
        code = re.sub(r"</?(?:code|span)(?:\s[^>]*)?>", "", code, flags=re.IGNORECASE)
        if "{%" in code or "{% endhighlight" in code:
            return m.group(0)
        if code.startswith("$"):
            lang = "bash"
        elif code.startswith("{") or code.startswith("["):
            lang = "json"
        elif "schema " in code or "rank-profile" in code or "field " in code:
            lang = "txt"
        else:
            lang = "txt"
        return f"\n```{lang}\n{code}\n```\n"

    return pattern.sub(to_fence, text)


def fix_img_tags(text: str) -> str:
    text = re.sub(
        r'<img\s+src="([^"]+)"\s+alt="([^"]*)"\s*width="[^"]*"\s*height="[^"]*"\s*/?>',
        r"\n<Frame>\n![\2](\1)\n</Frame>\n",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r'<img\s+src="([^"]+)"\s+alt="([^"]*)"\s*/?>',
        r"\n<Frame>\n![\2](\1)\n</Frame>\n",
        text,
        flags=re.IGNORECASE,
    )
    return text


def fix_angle_bracket_placeholders(text: str) -> str:
    text = text.replace("<host:port>", "`host:port`")
    return text


def wrap_inline_field_defs(text: str) -> str:
    def repl(m: re.Match) -> str:
        return f"`{m.group(0).strip()}`"

    return re.sub(
        r"^field \w+ type \w+ \{ indexing:[^}]+\}",
        repl,
        text,
        flags=re.MULTILINE,
    )


def html_tables_to_markdown(text: str) -> str:
    """Convert simple HTML tables to markdown."""

    def table_repl(m: re.Match) -> str:
        rows = re.findall(r"<tr>(.*?)</tr>", m.group(1), re.DOTALL)
        md_rows = []
        for row in rows:
            cells = re.findall(r"<t[dh]>(.*?)</t[dh]>", row, re.DOTALL)
            cells = [re.sub(r"<[^>]+>", "", c).strip() for c in cells]
            if not cells:
                continue
            cells = [
                c.replace("|", "\\|")
                .replace("<", "`<")
                .replace(">", ">`")
                if c in ("<", ">", "≤", "≥")
                else c
                for c in cells
            ]
            md_rows.append("| " + " | ".join(cells) + " |")
        if len(md_rows) >= 1:
            sep = "| " + " | ".join("---" for _ in md_rows[0].split("|")[1:-1]) + " |"
            if len(md_rows) > 1:
                return "\n" + md_rows[0] + "\n" + sep + "\n" + "\n".join(md_rows[1:]) + "\n"
        return m.group(0)

    return re.sub(
        r"<table[^>]*>(.*?)</table>",
        table_repl,
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )


def fix_bash_completion_redirect(text: str) -> str:
    """Lines like source <(cmd) break MDX."""
    if "vespa_completion" not in str(text):
        return text
    lines = []
    in_fence = False
    for line in text.split("\n"):
        if line.strip().startswith("```"):
            in_fence = not in_fence
            lines.append(line)
            continue
        if not in_fence and "<(" in line:
            lines.append("```bash")
            lines.append(line.strip())
            lines.append("```")
            continue
        lines.append(line)
    return "\n".join(lines)


def fix_tensor_pre_braces(text: str) -> str:
    """Content in pre blocks with {category: ...} - ensure inside fences."""
    return text  # handled by pre_parent_to_fences


def process_file(path: Path) -> bool:
    original = path.read_text(encoding="utf-8")
    text = original
    text = fix_frontmatter(text)
    text = jekyll_note_to_mdx(text)
    text = html_comments_to_mdx(text)
    text = pre_parent_to_fences(text)
    text = generic_pre_to_fences(text)
    text = jekyll_highlight_to_fences(text)
    text = escape_mdx_curly_in_math(text)
    text = fix_angle_in_tables(text)
    text = html_tables_to_markdown(text)
    text = fix_img_tags(text)
    text = fix_angle_bracket_placeholders(text)
    text = wrap_inline_field_defs(text)
    text = fix_bash_completion_redirect(text)
    if text != original:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def main() -> None:
    files = sorted(ROOT.rglob("*.md")) + sorted(ROOT.rglob("*.mdx"))
    count = 0
    for path in files:
        if process_file(path):
            print(f"Fixed {path.relative_to(ROOT.parent)}")
            count += 1
    print(f"Updated {count} files")


if __name__ == "__main__":
    main()
