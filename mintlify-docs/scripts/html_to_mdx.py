#!/usr/bin/env python3
"""Convert Vespa Jekyll HTML docs to Mintlify MDX."""

from __future__ import annotations

import html
import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path

APPS_DIR = Path(__file__).resolve().parent.parent / "en" / "applications"
VOID_TAGS = frozenset({"br", "hr", "img", "input", "meta", "link"})


@dataclass
class Node:
    tag: str | None = None
    attrs: dict[str, str] = field(default_factory=dict)
    children: list[Node | str] = field(default_factory=list)

    def text_content(self) -> str:
        parts: list[str] = []
        for c in self.children:
            if isinstance(c, str):
                parts.append(c)
            else:
                parts.append(c.text_content())
        return "".join(parts).strip()


class TreeBuilder(HTMLParser):
    def __init__(self) -> None:
        # Keep &lt;...&gt; in <pre> and tables; avoid treating placeholders as tags.
        super().__init__(convert_charrefs=False)
        self.root = Node(tag="root")
        self.stack: list[Node] = [self.root]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in VOID_TAGS:
            node = Node(tag=tag, attrs={k: v or "" for k, v in attrs})
            self.stack[-1].children.append(node)
            return
        node = Node(tag=tag, attrs={k: v or "" for k, v in attrs})
        self.stack[-1].children.append(node)
        self.stack.append(node)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in VOID_TAGS:
            return
        if len(self.stack) > 1:
            self.stack.pop()

    def handle_data(self, data: str) -> None:
        if data:
            self.stack[-1].children.append(data)

    def handle_entityref(self, name: str) -> None:
        self.stack[-1].children.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        self.stack[-1].children.append(f"&#{name};")


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    fm = text[3:end].strip()
    body = text[end + 4 :].lstrip("\n")
    meta: dict[str, str] = {}
    for line in fm.splitlines():
        if line.startswith("#") or not line.strip():
            continue
        if ":" in line:
            key, _, val = line.partition(":")
            meta[key.strip()] = val.strip().strip('"')
    return meta, body


def convert_href(href: str, source_dir: Path) -> str:
    if not href or href.startswith(("http://", "https://", "mailto:", "#")):
        return href
    if href.startswith("/"):
        parts = href.split("#", 1)
        path = parts[0].replace(".html", "")
        anchor = f"#{parts[1]}" if len(parts) > 1 else ""
        return path + anchor
    parts = href.split("#", 1)
    path = parts[0].replace(".html", "")
    anchor = f"#{parts[1]}" if len(parts) > 1 else ""
    resolved = (source_dir / path).resolve()
    try:
        rel = resolved.relative_to(APPS_DIR.parent.parent)
        return "/" + str(rel).replace("\\", "/") + anchor
    except ValueError:
        return path + anchor


def preprocess_body(body: str) -> str:
    # Unclosed <p> wrapping lists or trailing content
    body = re.sub(r"<p>((?:(?!</p>)[\s\S])*?)<ul>", r"<p>\1</p>\n<ul>", body, flags=re.IGNORECASE)
    body = re.sub(r"<p>((?:(?!</p>)[\s\S])*?)<ol>", r"<p>\1</p>\n<ol>", body, flags=re.IGNORECASE)
    body = re.sub(r"</ul>\s*</p>", "</ul>", body, flags=re.IGNORECASE)
    body = re.sub(r"</ol>\s*</p>", "</ol>", body, flags=re.IGNORECASE)
    body = re.sub(r"<p>\s*<ul>", "<ul>", body, flags=re.IGNORECASE)
    body = re.sub(r"<p>\s*<ol>", "<ol>", body, flags=re.IGNORECASE)
    body = re.sub(r"<i>", "<em>", body, flags=re.IGNORECASE)
    body = re.sub(r"</i>", "</em>", body, flags=re.IGNORECASE)

    def important_repl(m: re.Match) -> str:
        content = html.unescape(m.group(2)).strip()
        return f"<mdx-warning>{content}</mdx-warning>"

    def note_repl(m: re.Match) -> str:
        content = html.unescape(m.group(2)).strip()
        return f"<mdx-note>{content}</mdx-note>"

    body = re.sub(
        r"\{%\s*include\s+important\.html\s+content=(['\"])(.*?)\1\s*%\}",
        important_repl,
        body,
        flags=re.DOTALL,
    )
    body = re.sub(
        r"\{%\s*include\s+note\.html\s+content=(['\"])(.*?)\1\s*%\}",
        note_repl,
        body,
        flags=re.DOTALL,
    )
    body = re.sub(r"\{%\s*include\s+video-include\.html[^%]*%\}", "", body, flags=re.DOTALL)

    def deprecated_repl(m: re.Match) -> str:
        content = html.unescape(m.group(2)).strip()
        return f"<mdx-warning>{content}</mdx-warning>"

    body = re.sub(
        r"\{%\s*include\s+deprecated\.html\s+content=(['\"])(.*?)\1\s*%\}",
        deprecated_repl,
        body,
        flags=re.DOTALL,
    )
    body = re.sub(
        r"\{%\s*include\s+version\.html\s+version=[\"']([^\"']+)[\"']\s*%\}",
        lambda m: f"Vespa {m.group(1)}+",
        body,
    )
    body = re.sub(
        r'<span class="pre-hilite">(.*?)</span>',
        lambda m: f"<code>{html.unescape(m.group(1))}</code>",
        body,
        flags=re.DOTALL,
    )
    # Jekyll sources sometimes omit </li> before the next <li>
    body = re.sub(
        r"(<li>(?:(?!</li>)[\s\S])*?)(\s*<li>)",
        lambda m: m.group(1) + "</li>" + m.group(2),
        body,
    )

    def escape_pre_content(m: re.Match) -> str:
        inner = m.group(1)
        if "{%" in inner or "data-lang=" in inner:
            return m.group(0)
        if "&lt;" in inner:
            return m.group(0)
        escaped = inner.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return f"<pre>{escaped}</pre>"

    body = re.sub(
        r"<pre(?:\s[^>]*)?>(.*?)</pre>",
        escape_pre_content,
        body,
        flags=re.DOTALL | re.IGNORECASE,
    )

    def pre_highlight(m: re.Match) -> str:
        lang = m.group(1) or "txt"
        code = html.unescape(m.group(2)).strip("\n")
        escaped = html.escape(code, quote=False)
        return f'<pre data-lang="{lang}">{escaped}</pre>'

    body = re.sub(
        r"<pre>\s*\{%\s*highlight\s+(\w*)\s*%\}\s*(.*?)\s*\{%\s*endhighlight\s*%\}\s*</pre>",
        pre_highlight,
        body,
        flags=re.DOTALL,
    )
    body = re.sub(
        r"\{%\s*highlight\s+(\w*)\s*%\}\s*(.*?)\s*\{%\s*endhighlight\s*%\}",
        pre_highlight,
        body,
        flags=re.DOTALL,
    )

    def img_repl(m: re.Match) -> str:
        alt = m.group(1) or ""
        src = m.group(2)
        return f'<mdx-frame><img src="{src}" alt="{alt}"/></mdx-frame>'

    body = re.sub(
        r'<img\s+[^>]*src=["\']([^"\']+)["\'][^>]*alt=["\']([^"\']*)["\'][^>]*/?>',
        lambda m: f'<mdx-frame><img src="{m.group(1)}" alt="{m.group(2)}"/></mdx-frame>',
        body,
        flags=re.IGNORECASE,
    )
    body = re.sub(
        r'<img\s+[^>]*alt=["\']([^"\']*)["\'][^>]*src=["\']([^"\']+)["\'][^>]*/?>',
        lambda m: f'<mdx-frame><img src="{m.group(2)}" alt="{m.group(1)}"/></mdx-frame>',
        body,
        flags=re.IGNORECASE,
    )
    body = re.sub(
        r'<img\s+[^>]*src=["\']([^"\']+)["\'][^>]*/?>',
        lambda m: f'<mdx-frame><img src="{m.group(1)}" alt=""/></mdx-frame>',
        body,
        flags=re.IGNORECASE,
    )
    return body


BLOCK_IN_CELL = frozenset({"p", "ul", "ol", "pre", "table", "dl", "h2", "h3", "h4"})


def cell_has_blocks(node: Node) -> bool:
    for c in node.children:
        if isinstance(c, Node):
            if c.tag in BLOCK_IN_CELL or cell_has_blocks(c):
                return True
    return False


def table_has_rich_cells(node: Node) -> bool:
    for c in node.children:
        if isinstance(c, Node):
            if c.tag in ("td", "th") and cell_has_blocks(c):
                return True
            if table_has_rich_cells(c):
                return True
    return False


def attrs_str(attrs: dict[str, str]) -> str:
    if not attrs:
        return ""
    return " " + " ".join(f'{k}="{html.escape(v, quote=True)}"' for k, v in attrs.items())


def node_to_html(node: Node | str, source_dir: Path) -> str:
    if isinstance(node, str):
        return html.escape(html.unescape(node))
    tag = node.tag or ""
    if tag in VOID_TAGS:
        return f"<{tag}{attrs_str(node.attrs)}/>"
    inner = "".join(node_to_html(c, source_dir) for c in node.children)
    if tag == "a":
        href = convert_href(node.attrs.get("href", ""), source_dir)
        return f'<a href="{html.escape(href, quote=True)}">{inner}</a>'
    if tag == "code":
        return f"<code>{inner}</code>"
    if tag in ("em", "i"):
        return f"<em>{inner}</em>"
    if tag in ("strong", "b"):
        return f"<strong>{inner}</strong>"
    if tag == "br":
        return "<br/>"
    if tag == "pre":
        code = node.text_content()
        return f"<pre><code>{code}</code></pre>"
    if tag == "mdx-warning":
        return f"<Warning><strong>Important:</strong> {inner}</Warning>"
    if tag == "mdx-note":
        return f"<Note><strong>Note:</strong> {inner}</Note>"
    if tag == "p":
        text = "".join(
            node_to_html(c, source_dir) if isinstance(c, Node) else html.escape(html.unescape(c))
            for c in node.children
        ).strip()
        return f"<p>{text}</p>" if text else ""
    if tag == "ul":
        items = "".join(
            f"<li>{node_to_html(c, source_dir)}</li>"
            for c in node.children
            if isinstance(c, Node) and c.tag == "li"
        )
        return f"<ul>{items}</ul>"
    if tag == "li":
        return inner
    return f"<{tag}{attrs_str(node.attrs)}>{inner}</{tag}>"


def inline_md(node: Node | str, source_dir: Path) -> str:
    if isinstance(node, str):
        return html.unescape(node)
    tag = node.tag or ""
    kids = "".join(inline_md(c, source_dir) for c in node.children)

    if tag == "a":
        href = convert_href(node.attrs.get("href", ""), source_dir)
        text = kids.strip() or href
        return f"[{text}]({href})"
    if tag == "code":
        return f"`{kids}`"
    if tag in ("em", "i"):
        return f"*{kids}*"
    if tag in ("strong", "b"):
        return f"**{kids}**"
    if tag == "br":
        return "\n"
    if tag == "mdx-warning":
        return f"\n<Warning>\n**Important:**\n\n{kids.strip()}\n</Warning>\n"
    if tag == "mdx-note":
        return f"\n<Note>\n**Note:**\n\n{kids.strip()}\n</Note>\n"
    if tag == "mdx-frame":
        img = next((c for c in node.children if isinstance(c, Node) and c.tag == "img"), None)
        if img:
            alt = img.attrs.get("alt", "")
            src = img.attrs.get("src", "")
            return f"\n<Frame>\n![{alt}]({src})\n</Frame>\n"
    if tag == "img":
        alt = node.attrs.get("alt", "")
        src = node.attrs.get("src", "")
        return f"\n<Frame>\n![{alt}]({src})\n</Frame>\n"
    if tag in ("ul", "ol", "li", "p", "h1", "h2", "h3", "h4", "pre", "table", "tr", "td", "th"):
        return kids
    return kids


def block_md(node: Node, source_dir: Path, depth: int = 0) -> str:
    if isinstance(node, str):
        return html.unescape(node)
    tag = node.tag or ""
    indent = "  " * depth

    if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
        level = int(tag[1])
        text = inline_md(node, source_dir).strip()
        return f"\n{'#' * level} {text}\n\n"

    if tag == "p":
        text = inline_md(node, source_dir).strip()
        return f"{text}\n\n" if text else ""

    if tag == "pre":
        lang = node.attrs.get("data-lang", "txt") or "txt"
        code = html.unescape(node.text_content())
        return f"\n```{lang}\n{code}\n```\n\n"

    if tag == "ul":
        lines: list[str] = []
        for c in node.children:
            if isinstance(c, Node) and c.tag == "li":
                item = block_md(c, source_dir, depth).strip()
                item_lines = item.split("\n")
                lines.append(f"{indent}- {item_lines[0]}")
                for extra in item_lines[1:]:
                    lines.append(f"{indent}  {extra}")
        return "\n".join(lines) + "\n\n"

    if tag == "ol":
        lines = []
        n = 0
        for c in node.children:
            if isinstance(c, Node) and c.tag == "li":
                n += 1
                item = block_md(c, source_dir, depth).strip()
                item_lines = item.split("\n")
                lines.append(f"{indent}{n}. {item_lines[0]}")
                for extra in item_lines[1:]:
                    lines.append(f"{indent}   {extra}")
        return "\n".join(lines) + "\n\n"

    if tag == "li":
        parts: list[str] = []
        for c in node.children:
            if isinstance(c, Node) and c.tag in ("ul", "ol"):
                parts.append("\n" + block_md(c, source_dir, depth + 1).rstrip())
            elif isinstance(c, Node) and c.tag == "p":
                parts.append(inline_md(c, source_dir).strip())
            else:
                parts.append(inline_md(c, source_dir))
        return "".join(parts).strip()

    if tag == "table":
        if table_has_rich_cells(node):
            return "\n" + node_to_html(node, source_dir) + "\n\n"
        rows: list[list[str]] = []
        for c in node.children:
            if isinstance(c, Node) and c.tag in ("thead", "tbody", "tr"):
                if c.tag == "tr":
                    rows.append([inline_md(cell, source_dir).strip() for cell in c.children if isinstance(cell, Node) and cell.tag in ("td", "th")])
                else:
                    for row in c.children:
                        if isinstance(row, Node) and row.tag == "tr":
                            rows.append([inline_md(cell, source_dir).strip() for cell in row.children if isinstance(cell, Node) and cell.tag in ("td", "th")])
        if not rows:
            return ""
        out = ["| " + " | ".join(rows[0]) + " |", "| " + " | ".join("---" for _ in rows[0]) + " |"]
        for row in rows[1:]:
            while len(row) < len(rows[0]):
                row.append("")
            out.append("| " + " | ".join(row[: len(rows[0])]) + " |")
        return "\n".join(out) + "\n\n"

    if tag == "dl":
        parts: list[str] = []
        for c in node.children:
            if isinstance(c, Node) and c.tag == "dt":
                parts.append(f"\n#### {inline_md(c, source_dir).strip()}\n\n")
            elif isinstance(c, Node) and c.tag == "dd":
                for child in c.children:
                    if isinstance(child, Node):
                        parts.append(block_md(child, source_dir, depth))
                    else:
                        t = html.unescape(child).strip()
                        if t:
                            parts.append(t + "\n\n")
            elif isinstance(c, Node):
                parts.append(block_md(c, source_dir, depth))
        return "".join(parts)

    if tag in ("dt", "dd"):
        return ""

    if tag in ("thead", "tbody", "tr", "td", "th"):
        return ""

    if tag in ("mdx-warning", "mdx-note", "mdx-frame"):
        return inline_md(node, source_dir)

    if tag == "root":
        parts = []
        for c in node.children:
            if isinstance(c, Node):
                parts.append(block_md(c, source_dir, depth))
            else:
                t = html.unescape(c).strip()
                if t:
                    parts.append(t + "\n\n")
        result = "".join(parts)
        result = re.sub(r"\n{3,}", "\n\n", result)
        # Strip HTML-source indentation from prose lines
        result = re.sub(r"(?m)^  +(?![\s`-])", "", result)
        return result.strip() + "\n"

    # default: render children
    return "".join(
        block_md(c, source_dir, depth) if isinstance(c, Node) else html.unescape(c)
        for c in node.children
    )


def first_description(root: Node) -> str:
    for c in root.children:
        if isinstance(c, Node) and c.tag == "p":
            text = c.text_content()
            text = re.sub(r"\s+", " ", text).strip()
            if len(text) > 200:
                text = text[:197].rsplit(" ", 1)[0] + "..."
            return text
    return ""


def convert_file(path: Path) -> None:
    raw = path.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(raw)
    title = meta.get("title", path.stem.replace("-", " ").title())

    if path.suffix == ".md" and not body.strip().startswith("<"):
        # Pure markdown source
        mdx_body = body.strip() + "\n"
        desc_m = re.search(r"^([^\n#].+?\.)", mdx_body, re.MULTILINE)
        description = desc_m.group(1).strip() if desc_m else f"{title} in Vespa applications."
        out_path = path.with_suffix(".mdx")
        out_path.write_text(
            f'---\ntitle: "{title}"\ndescription: {description}\n---\n\n{mdx_body}',
            encoding="utf-8",
        )
        if path != out_path:
            path.unlink()
        print(f"Converted {path.name} -> {out_path.name}")
        return

    body = preprocess_body(body.strip())
    builder = TreeBuilder()
    builder.feed(f"<body>{body}</body>")
    builder.close()
    mdx_body = block_md(builder.root, path.parent)
    description = first_description(builder.root) or f"{title} in Vespa applications."

    out_path = path.with_suffix(".mdx")
    out_path.write_text(
        f'---\ntitle: "{title}"\ndescription: {description}\n---\n\n{mdx_body}',
        encoding="utf-8",
    )
    if path.suffix == ".html":
        path.unlink()
    elif path.suffix == ".md":
        path.unlink()
    print(f"Converted {path.name} -> {out_path.name}")


def main() -> None:
    for mdx in APPS_DIR.glob("*.mdx"):
        mdx.unlink()
    # Restore HTML from git if missing
    import subprocess

    html_files = list(APPS_DIR.glob("*.html"))
    if not html_files:
        subprocess.run(
            ["git", "checkout", "HEAD", "--", "en/applications/*.html"],
            cwd=APPS_DIR.parent.parent,
            check=False,
        )
    targets = sorted(APPS_DIR.glob("*.html"))
    zk = APPS_DIR / "using-zookeeper.md"
    if not zk.exists():
        subprocess.run(
            ["git", "show", "HEAD:en/applications/using-zookeeper.md"],
            cwd=APPS_DIR.parent.parent,
            capture_output=True,
            text=True,
            check=False,
        )
    if zk.exists():
        targets.append(zk)
    for p in targets:
        convert_file(p)


if __name__ == "__main__":
    main()
