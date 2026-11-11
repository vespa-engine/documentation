#!/usr/bin/env python3
"""Convert HTML tables in MDX files to Mintlify markdown tables."""

from __future__ import annotations

import html
import re
from pathlib import Path

from html_to_mdx import Node, TreeBuilder, convert_href, preprocess_body

TABLE_TAG_RE = re.compile(r"<table\b", re.IGNORECASE)
H2_HTML_RE = re.compile(r'<h2\s+id="[^"]*">\s*([^<]+?)\s*</h2>', re.IGNORECASE)
HR_RE = re.compile(r"<hr\s*/?>", re.IGNORECASE)


def fix_short_td_rows(html_text: str) -> str:
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

    return re.sub(r"<tr[\s\S]*?</tr>", repl, html_text, flags=re.IGNORECASE)


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
    if tag == "pre":
        code = html.unescape(node.text_content()).strip()
        if "\n" in code:
            return " ".join(f"`{line.strip()}`" for line in code.split("\n") if line.strip())
        return f"`{code}`"
    if tag in ("em", "i"):
        return f"*{inner}*"
    if tag in ("strong", "b"):
        return f"**{inner}**"
    if tag == "mdx-warning":
        return f"**Important:** {inner.strip()}"
    if tag == "mdx-note":
        return f"**Note:** {inner.strip()}"
    return inner


def table_end(html_text: str, start: int) -> int:
    j = html_text.find(">", start) + 1
    depth = 1
    while j < len(html_text) and depth > 0:
        next_open = html_text.find("<table", j)
        next_close = html_text.find("</table>", j)
        if next_close == -1:
            return len(html_text)
        if next_open != -1 and next_open < next_close:
            depth += 1
            j = html_text.find(">", next_open) + 1
        else:
            depth -= 1
            j = next_close + len("</table>")
    return j


def isolate_nested_tables(table_html: str) -> tuple[str, list[str]]:
    nested: list[str] = []
    first = TABLE_TAG_RE.search(table_html)
    if not first:
        return table_html, nested
    pos = first.end()
    while True:
        m = TABLE_TAG_RE.search(table_html[pos:])
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


def normalize_table_html(table_html: str) -> str:
    def fence_sub(m: re.Match) -> str:
        lang = m.group(1) or "txt"
        code = html.escape(m.group(2).strip("\n"))
        return f'<pre data-lang="{lang}">{code}</pre>'

    table_html = re.sub(r"```(\w*)\n([\s\S]*?)```", fence_sub, table_html)
    return preprocess_body(fix_html_structure(table_html))


def nested_table_to_md_html(table_html: str, source_dir: Path) -> str:
    header, body_rows = extract_rows(table_html, source_dir)
    if not header or not body_rows:
        return ""
    if len(header) == 4 and all(len(r) >= 4 for r in body_rows):
        return " ".join(
            f"`{row[0]}` → composite `{row[1]}`, tokenization `{row[2]}`, syntax `{row[3]}`"
            for row in body_rows
        )
    lines: list[str] = []
    for row in body_rows:
        while len(row) < len(header):
            row.append("")
        parts = [f"**{h}:** {v}" for h, v in zip(header, row) if v.strip()]
        if parts:
            lines.append("; ".join(parts))
    return "<br />".join(lines)


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
                parts.append(nested_table_to_md_html(node_to_html_table(node), source_dir))
            elif c.tag in ("ul", "ol"):
                for li in c.children:
                    if isinstance(li, Node) and li.tag == "li":
                        parts.append(emit_inline(li, source_dir).strip())
            elif c.tag == "p":
                text = emit_inline(c, source_dir).strip()
                if text:
                    parts.append(text)
            elif c.tag == "pre":
                text = emit_inline(c, source_dir).strip()
                if text:
                    parts.append(text)
            elif c.tag in ("mdx-warning", "mdx-note"):
                parts.append(emit_inline(c, source_dir).strip())
            else:
                text = emit_inline(c, source_dir).strip()
                if text:
                    parts.append(text)
    return " ".join(parts)


def node_to_html_table(node: Node) -> str:
    tag = node.tag or ""
    inner = "".join(node_to_html_table_part(c) for c in node.children)
    attrs = " ".join(f'{k}="{html.escape(v, quote=True)}"' for k, v in node.attrs.items())
    open_tag = f"<{tag} {attrs}>" if attrs else f"<{tag}>"
    return f"{open_tag}{inner}</{tag}>"


def node_to_html_table_part(node: Node | str) -> str:
    if isinstance(node, str):
        return html.unescape(node)
    tag = node.tag or ""
    inner = "".join(node_to_html_table_part(c) for c in node.children)
    attrs = " ".join(f'{k}="{html.escape(v, quote=True)}"' for k, v in node.attrs.items())
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


def infer_header(first_row: list[str]) -> list[str]:
    n = len(first_row)
    if n == 2:
        return ["Term", "Description"]
    if n == 3:
        return ["Name", "Default", "Description"]
    if n == 4:
        return ["Name", "Type", "Default", "Description"]
    return [f"Column {i + 1}" for i in range(n)]


def extract_rows(table_html: str, source_dir: Path) -> tuple[list[str], list[list[str]]]:
    table_html = normalize_table_html(table_html)
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
        if cells and any(c.strip() for c in cells):
            body_rows.append(cells)
    if not header and body_rows:
        header = infer_header(body_rows[0])
    return header, body_rows


def html_table_to_markdown(table_html: str, source_dir: Path) -> str:
    caption_m = re.search(r"<caption>([\s\S]*?)</caption>", table_html, re.I)
    caption = html.unescape(caption_m.group(1)).strip() if caption_m else ""
    header, body_rows = extract_rows(table_html, source_dir)
    if not header:
        return table_html
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
    if not fragment.strip():
        return ""
    work = preprocess_body(fragment.strip())
    builder = TreeBuilder()
    builder.feed(f"<div>{work}</div>")
    builder.close()
    parts: list[str] = []
    for c in builder.root.children:
        if not isinstance(c, Node):
            continue
        if c.tag == "div":
            for cc in c.children:
                if isinstance(cc, Node) and cc.tag == "p":
                    text = emit_inline(cc, source_dir).strip()
                    if text:
                        parts.append(text)
                elif isinstance(cc, Node) and cc.tag in ("ul", "ol"):
                    for li in cc.children:
                        if isinstance(li, Node) and li.tag == "li":
                            parts.append(f"- {emit_inline(li, source_dir).strip()}")
        elif c.tag == "p":
            text = emit_inline(c, source_dir).strip()
            if text:
                parts.append(text)
    return "\n\n".join(parts) + ("\n\n" if parts else "")


def extract_all_tables(fragment: str) -> list[tuple[int, int, str]]:
    tables: list[tuple[int, int, str]] = []
    pos = 0
    while True:
        m = TABLE_TAG_RE.search(fragment[pos:])
        if not m:
            break
        start = pos + m.start()
        end = table_end(fragment, start)
        tables.append((start, end, fragment[start:end]))
        pos = end
    return tables


def convert_html_fragment(fragment: str, source_dir: Path) -> str:
    fragment = H2_HTML_RE.sub(r"## \1\n\n", fragment)
    out: list[str] = []
    pos = 0
    for start, end, table_html in extract_all_tables(fragment):
        before = fragment[pos:start]
        if before.strip():
            out.append(inline_html_to_md(before, source_dir))
        md = html_table_to_markdown(table_html, source_dir)
        if md and not md.startswith("<table"):
            out.append(md)
        else:
            out.append(table_html)
        pos = end
    rest = fragment[pos:]
    if rest.strip():
        out.append(inline_html_to_md(rest, source_dir))
    text = "".join(out)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def split_frontmatter(text: str) -> tuple[str, str]:
    if not text.startswith("---"):
        return "", text
    m = re.match(r"^---\r?\n(.*?)\r?\n---(?:\r?\n|$)", text, re.DOTALL)
    if not m:
        return "", text
    return text[: m.end()], text[m.end() :]


def convert_mdx_file(path: Path) -> bool:
    original = path.read_text(encoding="utf-8")
    if "<table" not in original.lower():
        return False
    fm, body = split_frontmatter(original)
    converted = convert_html_fragment(body, path.parent)
    if converted == body:
        return False
    fm_out = fm.rstrip("\n") + "\n"
    body_out = converted.lstrip("\n")
    path.write_text(fm_out + body_out, encoding="utf-8")
    return True


def convert_tree(root: Path) -> int:
    count = 0
    for path in sorted(root.rglob("*.mdx")):
        if convert_mdx_file(path):
            print(f"Converted tables in {path.relative_to(root.parent.parent)}")
            count += 1
    return count
