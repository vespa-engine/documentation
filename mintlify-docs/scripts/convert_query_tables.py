#!/usr/bin/env python3
"""Convert query API reference HTML tables to Mintlify markdown tables."""

from __future__ import annotations

import html
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from html_to_mdx import Node, TreeBuilder, convert_href, preprocess_body  # noqa: E402

SOURCE_DIR = Path(__file__).resolve().parent.parent / "en" / "reference" / "api"
ROOT = SOURCE_DIR.parent.parent

H2_RE = re.compile(r'<h2\s+id="([^"]*)"[^>]*>([^<]*)</h2>', re.I)
TABLE_CLASS_RE = re.compile(r"<table\s+class=\"table\"", re.I)
P_RE = re.compile(r"<p(?:\s[^>]*)?>(.*?)</p>", re.I | re.DOTALL)
HR_RE = re.compile(r"<hr\s*/?>", re.I)


def load_html_section() -> str:
    raw = subprocess.check_output(
        ["git", "show", "HEAD:en/reference/api/query.html"],
        cwd=ROOT,
        text=True,
    )
    idx = raw.find('<h2 id="query">')
    if idx == -1:
        raise SystemExit("query section not found in HTML")
    return raw[idx:]


def fix_short_td_rows(html: str) -> str:
    """Fix rows like <tr><td>a<td>b</tr> missing </td> closers."""

    def repl(m: re.Match) -> str:
        row = m.group(0)
        if "</td>" in row or "</th>" in row:
            return row
        pieces = re.split(r"(?=<t[dh]\b)", row)
        out = [pieces[0]]
        for piece in pieces[1:]:
            tag_m = re.match(r"(<t[dh][^>]*>)([\s\S]*)", piece, re.I)
            if not tag_m:
                continue
            tag, rest = tag_m.groups()
            content = re.split(r"(?=</tr>)", rest, maxsplit=1)[0].strip()
            close = "</th>" if tag.lower().startswith("<th") else "</td>"
            out.append(f"{tag}{content}{close}")
        if "</tr>" in row and not out[-1].endswith("</tr>"):
            out.append("</tr>")
        return "".join(out)

    return re.sub(r"<tr[\s\S]*?</tr>", repl, html, flags=re.IGNORECASE)


def fix_html_structure(body: str) -> str:
    body = re.sub(
        r"(<p(?:\s[^>]*)?>(?:(?!</p>)[\s\S])*?)(\s*</td>)",
        r"\1</p>\2",
        body,
        flags=re.IGNORECASE,
    )
    body = re.sub(
        r"(<li>(?:(?!</li>)[\s\S])*?)(\s*<li>)",
        lambda m: m.group(1) + "</li>" + m.group(2),
        body,
    )
    body = fix_short_td_rows(body)
    body = re.sub(
        r"<tr><th rowspan=\"2\">Value\s*<th colspan=\"3\">Results in</tr>\s*"
        r"<tr>\s*(?:<th>)?composite</th><th>tokenization</th><th>syntax</th></tr>",
        "<tr><th>Value</th><th>composite</th><th>tokenization</th><th>syntax</th></tr>",
        body,
        flags=re.IGNORECASE,
    )
    # Close table rows that end at </table> without </tr>
    body = re.sub(
        r"(<tr>(?:(?!</tr>)[\s\S])*?)(</table>)",
        lambda m: m.group(1) + "</td></tr>" + m.group(2),
        body,
        flags=re.IGNORECASE,
    )
    return body


def escape_cell(text: str) -> str:
    text = text.replace("\n", " ").replace("\r", "")
    text = re.sub(r"\s+", " ", text).strip()
    return text.replace("|", "\\|")


def emit_inline(node: Node | str, source_dir: Path) -> str:
    if isinstance(node, str):
        return html.unescape(node)
    tag = node.tag or ""
    inner = "".join(emit_inline(c, source_dir) for c in node.children)
    if tag == "br":
        return "<br />"
    if tag == "a":
        href = convert_href(node.attrs.get("href", ""), source_dir)
        text = inner.strip() or href
        return f"[{text}]({href})"
    if tag == "code":
        return f"`{inner}`"
    if tag in ("em", "i"):
        return f"*{inner}*"
    if tag in ("strong", "b"):
        return f"**{inner}**"
    if tag == "mdx-warning":
        return f"**Important:** {inner.strip()}"
    if tag == "mdx-note":
        return f"**Note:** {inner.strip()}"
    return inner


def nested_table_to_md(node: Node, source_dir: Path) -> str:
    rows: list[list[str]] = []
    for c in node.children:
        if isinstance(c, Node) and c.tag == "tr":
            cells = [
                escape_cell(emit_inline(cell, source_dir))
                for cell in c.children
                if isinstance(cell, Node) and cell.tag in ("td", "th")
            ]
            if cells:
                rows.append(cells)
    if not rows:
        return ""
    if len(rows[0]) == 2:
        return " ".join(f"`{r[0]}`: {r[1]}" for r in rows)
    return " ".join(" — ".join(r) for r in rows)


def emit_cell(node: Node, source_dir: Path) -> str:  # noqa: PLR0912
    parts: list[str] = []
    for c in node.children:
        if isinstance(c, Node):
            if c.tag == "table":
                nested = nested_table_to_md(c, source_dir)
                if nested:
                    parts.append(nested)
            elif c.tag in ("ul", "ol"):
                for li in c.children:
                    if isinstance(li, Node) and li.tag == "li":
                        parts.append(emit_inline(li, source_dir).strip())
            elif c.tag == "p":
                text = emit_inline(c, source_dir).strip()
                if text:
                    parts.append(text)
            elif c.tag in ("mdx-warning", "mdx-note"):
                parts.append(emit_inline(c, source_dir).strip())
            else:
                text = emit_inline(c, source_dir).strip()
                if text:
                    parts.append(text)
        else:
            t = html.unescape(c).strip()
            if t:
                parts.append(t)
    return " ".join(parts)


def row_cells(tr: Node) -> list[Node]:
    return [c for c in tr.children if isinstance(c, Node) and c.tag in ("th", "td")]


def cell_text(cell: Node, source_dir: Path) -> str:
    if cell.tag == "th":
        return escape_cell(emit_inline(cell, source_dir))
    return escape_cell(emit_cell(cell, source_dir))


NESTED_TABLE_RE = re.compile(r"<table[^>]*>[\s\S]*?</table>", re.IGNORECASE)


def table_end(html: str, start: int) -> int:
    j = html.find(">", start) + 1
    depth = 1
    while j < len(html) and depth > 0:
        next_open = html.find("<table", j)
        next_close = html.find("</table>", j)
        if next_close == -1:
            return len(html)
        if next_open != -1 and next_open < next_close:
            depth += 1
            j = html.find(">", next_open) + 1
        else:
            depth -= 1
            j = next_close + len("</table>")
    return j


def isolate_nested_tables(table_html: str) -> tuple[str, list[str]]:
    """Replace every nested <table> inside the outer table with placeholders."""
    nested: list[str] = []
    first = re.search(r"<table\b", table_html, re.I)
    if not first:
        return table_html, nested
    pos = first.end()
    while True:
        m = re.search(r"<table\b", table_html[pos:], re.I)
        if not m:
            break
        start = pos + m.start()
        end = table_end(table_html, start)
        nested.append(table_html[start:end])
        placeholder = f"<!--NESTED{len(nested) - 1}-->"
        table_html = table_html[:start] + placeholder + table_html[end:]
        pos = start + len(placeholder)
    return table_html, nested


def restore_nested(fragment: str, nested: list[str]) -> str:
    for i, table_html in enumerate(nested):
        fragment = fragment.replace(f"<!--NESTED{i}-->", table_html)
    return fragment


def nested_table_to_md_html(table_html: str, source_dir: Path) -> str:
    table_html = fix_short_td_rows(table_html)
    rows: list[list[str]] = []
    for tr in re.finditer(r"<tr[^>]*>([\s\S]*?)</tr>", table_html, re.I):
        cells = tr_cells_from_inner(tr.group(1), [], source_dir)
        if cells:
            rows.append(cells)
    if not rows:
        return ""
    if rows and all(len(r) == 2 for r in rows):
        return " ".join(f"`{r[0]}`: {r[1]}" for r in rows)
    if rows and all(len(r) >= 4 for r in rows):
        header = rows[0]
        parts = []
        for row in rows[1:]:
            parts.append(
                f"`{row[0]}` → composite `{row[1]}`, tokenization `{row[2]}`, syntax `{row[3]}`"
            )
        return " ".join(parts)
    if len(rows) >= 2 and len(rows[0]) >= 3:
        parts = []
        for row in rows[1:]:
            if len(row) >= 4:
                parts.append(
                    f"`{row[0]}` → composite `{row[1]}`, tokenization `{row[2]}`, syntax `{row[3]}`"
                )
            elif len(row) >= 2:
                parts.append(f"`{row[0]}`: {row[1]}")
        return " ".join(parts)
    return " ".join(" — ".join(r) for r in rows)


def html_inline_to_md(fragment: str, source_dir: Path) -> str:
    if not fragment.strip():
        return ""
    work = preprocess_body(fragment.strip())
    builder = TreeBuilder()
    builder.feed(f"<div>{work}</div>")
    builder.close()
    div = next(c for c in builder.root.children if isinstance(c, Node))
    return emit_cell(div, source_dir)


def emit_cell_node(node: Node, source_dir: Path, nested: list[str] | None = None) -> str:
    parts: list[str] = []
    for c in node.children:
        if isinstance(c, str):
            text = c.strip()
            for m in re.finditer(r"<!--NESTED(\d+)-->", text):
                if nested:
                    parts.append(nested_table_to_md_html(nested[int(m.group(1))], source_dir))
            text = re.sub(r"<!--NESTED\d+-->", "", text).strip()
            if text:
                parts.append(html.unescape(text))
        elif isinstance(c, Node):
            if c.tag == "table":
                parts.append(nested_table_to_md_html(node_to_html_table(c), source_dir))
            elif c.tag in ("ul", "ol"):
                for li in c.children:
                    if isinstance(li, Node) and li.tag == "li":
                        parts.append(emit_inline(li, source_dir).strip())
            elif c.tag == "p":
                text = emit_inline(c, source_dir).strip()
                if text:
                    parts.append(text)
            elif c.tag in ("mdx-warning", "mdx-note"):
                parts.append(emit_inline(c, source_dir).strip())
            else:
                text = emit_inline(c, source_dir).strip()
                if text:
                    parts.append(text)
        else:
            t = html.unescape(c).strip()
            if t:
                parts.append(t)
    return " ".join(parts)


def node_to_html_table(node: Node) -> str:
    return "".join(node_to_html_table_part(c) for c in [node])


def node_to_html_table_part(node: Node | str) -> str:
    if isinstance(node, str):
        return html.unescape(node)
    tag = node.tag or ""
    inner = "".join(node_to_html_table_part(c) for c in node.children)
    attrs = " ".join(f'{k}="{v}"' for k, v in node.attrs.items())
    open_tag = f"<{tag} {attrs}>" if attrs else f"<{tag}>"
    return f"{open_tag}{inner}</{tag}>"


def tr_cells_from_inner(tr_inner: str, nested: list[str], source_dir: Path) -> list[str]:
    inner = restore_nested(tr_inner, nested)
    builder = TreeBuilder()
    builder.feed(f"<tr>{inner}</tr>")
    builder.close()
    tr = next(c for c in builder.root.children if isinstance(c, Node) and c.tag == "tr")
    cells: list[str] = []
    for c in tr.children:
        if isinstance(c, Node) and c.tag == "th":
            cells.append(escape_cell(emit_inline(c, source_dir)))
        elif isinstance(c, Node) and c.tag == "td":
            cells.append(escape_cell(emit_cell_node(c, source_dir, nested)))
    return cells


def extract_rows_regex(table_html: str, source_dir: Path) -> tuple[list[str], list[list[str]]]:
    header: list[str] = []
    body_rows: list[list[str]] = []
    isolated, nested = isolate_nested_tables(table_html)
    thead = re.search(r"<thead>([\s\S]*?)</thead>", isolated, re.I)
    if thead:
        htr = re.search(r"<tr[^>]*>([\s\S]*?)</tr>", thead.group(1), re.I)
        if htr:
            header = tr_cells_from_inner(htr.group(1), [], source_dir)
    tbody = re.search(r"<tbody>([\s\S]*?)</tbody>", isolated, re.I)
    chunk = tbody.group(1) if tbody else isolated
    for tr in re.finditer(r"<tr[^>]*>([\s\S]*?)</tr>", chunk, re.I):
        cells = tr_cells_from_inner(tr.group(1), nested, source_dir)
        if cells:
            body_rows.append(cells)
    return header, body_rows


def html_table_to_markdown(table_html: str, source_dir: Path) -> str:
    caption_m = re.search(r"<caption>([\s\S]*?)</caption>", table_html, re.I)
    caption = html.unescape(caption_m.group(1)).strip() if caption_m else ""

    header, body_rows = extract_rows_regex(table_html, source_dir)

    if not header:
        return ""

    ncol = len(header)
    lines: list[str] = []
    if caption:
        lines.extend([f"*{caption}*", ""])
    lines.append("| " + " | ".join(header) + " |")
    lines.append("| " + " | ".join("---" for _ in header) + " |")
    for row in body_rows:
        while len(row) < ncol:
            row.append("")
        lines.append("| " + " | ".join(row[:ncol]) + " |")
    return "\n".join(lines) + "\n\n"


def inline_html_to_md(fragment: str, source_dir: Path) -> str:
    fragment = preprocess_body(fragment.strip())
    builder = TreeBuilder()
    builder.feed(f"<div>{fragment}</div>")
    builder.close()
    parts: list[str] = []
    for c in builder.root.children:
        if isinstance(c, Node) and c.tag == "div":
            for cc in c.children:
                if isinstance(cc, Node) and cc.tag == "p":
                    text = emit_inline(cc, source_dir).strip()
                    if text:
                        parts.append(text)
                elif isinstance(cc, Node) and cc.tag in ("ul", "ol"):
                    for li in cc.children:
                        if isinstance(li, Node) and li.tag == "li":
                            parts.append(f"- {emit_inline(li, source_dir).strip()}")
        elif isinstance(c, Node) and c.tag == "p":
            text = emit_inline(c, source_dir).strip()
            if text:
                parts.append(text)
    return "\n\n".join(parts) + ("\n\n" if parts else "")


def convert_section(chunk: str, source_dir: Path) -> str:
    out: list[str] = []
    pos = 0
    for m in H2_RE.finditer(chunk):
        before = chunk[pos : m.start()]
        if before.strip():
            out.append(process_between(before, source_dir))
        title = html.unescape(m.group(2)).strip()
        out.append(f"## {title}\n\n")
        pos = m.end()

    tail = chunk[pos:]
    if tail.strip():
        out.append(process_between(tail, source_dir))
    return "".join(out)


def extract_main_tables(fragment: str) -> list[tuple[int, int, str]]:
    tables: list[tuple[int, int, str]] = []
    pos = 0
    while True:
        m = TABLE_CLASS_RE.search(fragment, pos)
        if not m:
            break
        start = m.start()
        j = fragment.find(">", m.end()) + 1
        depth = 1
        while j < len(fragment) and depth > 0:
            next_open = fragment.find("<table", j)
            next_close = fragment.find("</table>", j)
            if next_close == -1:
                break
            if next_open != -1 and next_open < next_close:
                depth += 1
                j = fragment.find(">", next_open) + 1
            else:
                depth -= 1
                j = next_close + len("</table>")
        if depth == 0:
            tables.append((start, j, fragment[start:j]))
            pos = j
        else:
            break
    return tables


def process_between(fragment: str, source_dir: Path) -> str:
    out: list[str] = []
    pos = 0
    for start, end, table_html in extract_main_tables(fragment):
        before = fragment[pos:start]
        if before.strip():
            out.append(inline_html_to_md(before, source_dir))
        out.append(html_table_to_markdown(table_html, source_dir))
        pos = end
    rest = fragment[pos:]
    if rest.strip():
        out.append(inline_html_to_md(rest, source_dir))
    if HR_RE.search(fragment) and "---" not in "".join(out):
        out.append("---\n\n")
    return "".join(out)


def convert() -> str:
    body = fix_html_structure(load_html_section())
    body = preprocess_body(body.strip())
    text = convert_section(body, SOURCE_DIR)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


def main() -> None:
    mdx_path = SOURCE_DIR / "query.mdx"
    original = mdx_path.read_text(encoding="utf-8")
    lines = original.split("\n")
    cut = next(i for i, line in enumerate(lines) if line.strip() == "## Query" and i > 20)
    head = "\n".join(lines[:cut])
    new_body = convert()
    mdx_path.write_text(f"{head}\n\n{new_body}", encoding="utf-8")
    print(f"Wrote {mdx_path} ({len(mdx_path.read_text().splitlines())} lines)")


if __name__ == "__main__":
    main()
