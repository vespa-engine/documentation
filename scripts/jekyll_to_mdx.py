#!/usr/bin/env python3
"""Convert the Jekyll documentation sources (en/**/*.html, en/**/*.md) to Mintlify MDX.

The output should need no manual fixes: it must be valid MDX, and render the same
content as the Jekyll page. scripts/compare_with_branch.py measures how close the
output is to the hand-fixed pages on the mintlify/migration branch.

Conventions:
- Frontmatter: title, plus sidebarTitle when the name in _data/sidebar.yml differs.
- Prose is Markdown with one line per paragraph. Tables are
  <table className="vespa-table"> JSX; cells with block content (code, lists,
  nested tables) use Markdown blocks inside the cell.
- All code is fenced, also inside table cells. Lines highlighted with
  <span class="pre-hilite"> become highlight={...}.
- {% include note|important|warning|deprecated %} become <Note>/<Warning>/<Danger>
  with the Jekyll label ("**Note:**") as the first line.
- MathML becomes $...$ / $$...$$ LaTeX.

Templates (_includes), data (_data) and site variables (_config.yml) are read from
the git ref holding the sources, origin/master by default.

Usage:
    scripts/jekyll_to_mdx.py en/applications/bundles.html   # convert from origin/master into the working tree
    scripts/jekyll_to_mdx.py --stdout en/ranking/bm25.html
"""

from __future__ import annotations

import argparse
import csv
import html
import io
import posixpath
import re
import subprocess
import sys
from dataclasses import dataclass, field
from functools import cache
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REF = "origin/master"

# ---------------------------------------------------------------------------
# Site context: files from the source ref


@cache
def ref_file(path: str) -> str | None:
    r = subprocess.run(["git", "show", f"{REF}:{path}"], cwd=ROOT, capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


@cache
def ref_listing(directory: str) -> tuple[str, ...]:
    r = subprocess.run(
        ["git", "ls-tree", "--name-only", f"{REF}:{directory}"], cwd=ROOT, capture_output=True, text=True
    )
    return tuple(r.stdout.split()) if r.returncode == 0 else ()


@cache
def site_variables() -> dict[str, str]:
    text = ref_file("_config.yml") or ""
    m = re.search(r"^variables:\n((?:[ \t]+.*\n?)*)", text, re.M)
    out = {}
    for line in (m.group(1) if m else "").splitlines():
        k, _, v = line.strip().partition(":")
        if k:
            out[k.strip()] = v.strip().strip("\"'")
    return out


def read_csv(path: str) -> list[dict[str, str]]:
    text = ref_file(path)
    return list(csv.DictReader(io.StringIO(text))) if text else []


def site_data(name: str):
    """site.data.<name>: a CSV file as a list of rows, or a directory as a dict of those."""
    if ref_file(f"_data/{name}.csv") is not None:
        return read_csv(f"_data/{name}.csv")
    files = ref_listing(f"_data/{name}")
    return {f[:-4]: read_csv(f"_data/{name}/{f}") for f in files if f.endswith(".csv")}


def page_path(url: str) -> str:
    """/en/foo.html, /en/foo.md, /en/foo/ or /en/foo/index.html -> /en/foo"""
    url = re.sub(r"(/index)?\.(html|md)$", "", url)
    return url.rstrip("/") if len(url) > 1 else url


@cache
def redirects() -> dict[str, str]:
    """Old page path -> the page it redirects to, following chains."""
    pairs = {}
    for line in (ref_file("redirects.yml") or "").splitlines():
        m = re.match(r"\s*([^#\s][^:]*):\s*(\S+)", line)
        if m:
            pairs[page_path(m.group(1).strip())] = page_path(m.group(2).strip())
    resolved = {}
    for src in pairs:
        dst, seen = pairs[src], {src}
        while dst in pairs and dst not in seen:
            seen.add(dst)
            dst = pairs[dst]
        resolved[src] = dst
    return resolved


@cache
def sidebar_names() -> dict[str, str]:
    """Page path (en/foo/bar) -> the page name in _data/sidebar.yml."""
    names, page = {}, None
    for line in (ref_file("_data/sidebar.yml") or "").splitlines():
        m = re.match(r"\s*-?\s*page:\s*(.+)", line)
        if m:
            page = m.group(1).strip().strip("\"'")
            continue
        m = re.match(r"\s*url:\s*(\S+)", line)
        if m and page:
            url = m.group(1).split("#")[0]
            url = re.sub(r"(/index)?\.html$", "", url).strip("/")
            names.setdefault(url, page)
            page = None
    return names


# ---------------------------------------------------------------------------
# Liquid

# Private-use characters mark code blocks from {% highlight %} through later stages.
HL_START, HL_SEP, HL_END = "", "", ""
CALLOUT_KINDS = {
    "note": ("Note", "Note"),
    "important": ("Warning", "Important"),
    "warning": ("Warning", "Warning"),
    "deprecated": ("Danger", "Deprecated"),
}
CHIPS = {
    "chip-cloud": ("Vespa Cloud", "This content is applicable to Vespa Cloud deployments."),
    "chip-self-managed": ("Self-managed", "This content is applicable to self-managed Vespa systems."),
    "chip-enterprise": ("Enterprise", "Not open source: This functionality is only available commercially."),
}

TOKEN_RE = re.compile(r"\{%-?\s*(.*?)\s*-?%\}|\{\{-?\s*(.*?)\s*-?\}\}", re.DOTALL)


@dataclass
class LiquidOptions:
    markdown: bool  # the page is Markdown: includes emit Markdown instead of HTML


def liquid(text: str, opts: LiquidOptions, scope: dict | None = None) -> str:
    scope = dict(scope or {})
    tokens = tokenize(text)
    out, _ = render_tokens(tokens, 0, scope, opts, stop=())
    return out


def tokenize(text: str) -> list[tuple[str, str]]:
    tokens: list[tuple[str, str]] = []
    pos = 0
    raw_re = re.compile(r"\{%-?\s*raw\s*-?%\}(.*?)\{%-?\s*endraw\s*-?%\}", re.DOTALL)
    while pos < len(text):
        m = TOKEN_RE.search(text, pos)
        r = raw_re.search(text, pos)
        if r and (not m or r.start() <= m.start()):
            tokens.append(("text", text[pos : r.start()]))
            tokens.append(("text", r.group(1)))
            pos = r.end()
            continue
        if not m:
            tokens.append(("text", text[pos:]))
            break
        tokens.append(("text", text[pos : m.start()]))
        tokens.append(("tag", m.group(1)) if m.group(1) is not None else ("var", m.group(2)))
        pos = m.end()
    return tokens


def render_tokens(tokens, i, scope, opts, stop):
    out: list[str] = []
    while i < len(tokens):
        kind, value = tokens[i]
        if kind == "text":
            out.append(value)
            i += 1
            continue
        if kind == "var":
            out.append(str(evaluate(value, scope)))
            i += 1
            continue
        name, _, args = value.partition(" ")
        if name in stop:
            return "".join(out), i
        i += 1
        if name == "comment":
            _, i = render_tokens(tokens, i, scope, opts, stop=("endcomment",))
            i += 1
        elif name == "assign":
            var, _, expr = args.partition("=")
            scope[var.strip()] = evaluate(expr, scope)
        elif name == "for":
            m = re.match(r"(\w+)\s+in\s+(.+)", args.strip())
            start = i
            items = evaluate(m.group(2), scope) if m else []
            if isinstance(items, dict):
                items = list(items.items())
            end = start
            for n, item in enumerate(items or []):
                inner = dict(scope, **{m.group(1): item, "forloop": {"index0": n, "index": n + 1}})
                body, end = render_tokens(tokens, start, inner, opts, stop=("endfor",))
                out.append(body)
            if not items:
                _, end = render_tokens(tokens, start, dict(scope), opts, stop=("endfor",))
            i = end + 1
        elif name == "highlight":
            body, i = render_tokens(tokens, i, scope, opts, stop=("endhighlight",))
            i += 1
            lang = args.split()[0] if args.split() else ""
            out.append(f"{HL_START}{lang}{HL_SEP}{body.strip(chr(10))}{HL_END}")
        elif name == "include":
            out.append(render_include(args, scope, opts))
        elif name in ("if", "unless", "case"):
            # Not used by the documentation pages; render the first branch.
            body, i = render_tokens(tokens, i, scope, opts, stop=("elsif", "else", "endif", "endunless", "endcase"))
            while i < len(tokens) and tokens[i][1].split(" ")[0] not in ("endif", "endunless", "endcase"):
                i += 1
            i += 1
            out.append(body)
        # other tags (e.g. endraw without raw) are dropped
    return "".join(out), i


def evaluate(expr: str, scope: dict):
    parts = [p.strip() for p in expr.split("|")]
    value = lookup(parts[0], scope)
    for f in parts[1:]:
        fname, _, farg = f.partition(":")
        farg_v = lookup(farg.strip(), scope) if farg else None
        if fname.strip() == "split" and isinstance(value, str):
            value = value.split(farg_v)
    return "" if value is None else value


def lookup(expr: str, scope: dict):
    expr = expr.strip()
    if not expr:
        return None
    if expr[0] in "\"'" and expr[-1] == expr[0]:
        return expr[1:-1]
    if re.fullmatch(r"-?\d+", expr):
        return int(expr)
    parts = re.findall(r"[\w-]+|\[[^\]]+\]", expr)
    if not parts:
        return None
    if parts[0] == "site":
        if len(parts) >= 3 and parts[1] == "variables":
            return site_variables().get(parts[2].strip("[]\"'"), "")
        if len(parts) >= 3 and parts[1] == "data":
            value = site_data(parts[2])
            rest = parts[3:]
        else:
            return ""
    else:
        value = scope.get(parts[0])
        rest = parts[1:]
    for p in rest:
        key = p[1:-1] if p.startswith("[") else p
        key_v = lookup(key, scope) if p.startswith("[") and key[0] not in "\"'" else key.strip("\"'")
        if isinstance(value, dict):
            value = value.get(key_v)
        elif isinstance(value, list) and isinstance(key_v, int):
            value = value[key_v] if -len(value) <= key_v < len(value) else None
        else:
            return None
    return value


INCLUDE_ARG_RE = re.compile(r"""([\w-]+)=("((?:\\.|[^"\\])*)"|'((?:\\.|[^'\\])*)'|(\S+))""", re.DOTALL)


def render_include(args: str, scope: dict, opts: LiquidOptions) -> str:
    name, _, rest = args.strip().partition(" ")
    params = {}
    for m in INCLUDE_ARG_RE.finditer(rest):
        if m.group(3) is not None or m.group(4) is not None:
            # quoted: Jekyll allows backslash-escaped quotes
            v = re.sub(r"\\([\"'])", r"\1", m.group(3) if m.group(3) is not None else m.group(4))
        else:
            v = lookup(m.group(5), scope)
        params[m.group(1)] = v
    base = name.removesuffix(".html")
    content = liquid(str(params.get("content", "")), opts, scope)
    if base in CALLOUT_KINDS:
        if opts.markdown:
            component, label = CALLOUT_KINDS[base]
            return f"\n\n<{component}>\n**{label}:**\n\n{content.strip()}\n</{component}>\n\n"
        return f'<x-callout kind="{base}">{content}</x-callout>'
    if base == "version":
        v = params.get("version", "")
        return f"`Vespa {v}+`" if opts.markdown else f"<x-version>Vespa {v}+</x-version>"
    if base in CHIPS:
        return f'<x-chip name="{base}"></x-chip>'
    if base == "video-include":
        return ""
    template = ref_file(f"_includes/{name}")
    if template is None:
        return ""
    return liquid(template, opts, dict(scope, include=params))


# ---------------------------------------------------------------------------
# Links


def convert_href(href: str, source: str) -> str:
    """Jekyll link -> Mintlify link. `source` is the repo path of the page."""
    href = href.strip()
    if not href or href.startswith(("#", "mailto:", "javascript:")) or re.match(r"\w+://", href):
        return href
    path, sep, anchor = href.partition("#")
    if not path.startswith("/"):
        path = posixpath.normpath(posixpath.join("/" + posixpath.dirname(source), path))
    if re.search(r"\.(html|md)$|/$", path) or not re.search(r"\.\w+$", path):
        path = page_path(path)
        path = redirects().get(path, path)
    return path + (sep + anchor if sep else "")


def md_link_target(href: str) -> str:
    """A Markdown link destination; MDX has no <...> autolinks, so avoid angle brackets."""
    href = href.replace(" ", "%20").replace("<", "%3C").replace(">", "%3E")
    depth = 0
    for ch in href:
        depth += {"(": 1, ")": -1}.get(ch, 0)
        if depth < 0:
            break
    if depth != 0:
        href = href.replace("(", "%28").replace(")", "%29")
    return href


# ---------------------------------------------------------------------------
# Markdown text escaping


def escape_text(text: str) -> str:
    """Escape prose so it renders literally in MDX."""
    out = []
    for i, ch in enumerate(text):
        prev = text[i - 1] if i else " "
        nxt = text[i + 1] if i + 1 < len(text) else " "
        if ch in "\\`*[]{}":
            out.append("\\" + ch)
        elif ch == "_" and not (prev.isalnum() and nxt.isalnum()):
            out.append("\\_")
        elif ch == "<":
            out.append("&lt;")
        elif ch == ">":
            out.append("&gt;")
        elif ch == "&" and re.match(r"&(#\d+|#x[0-9a-fA-F]+|\w+);", text[i:]):
            out.append("&amp;")
        elif ch == "~" and nxt == "~":
            out.append("\\~")
        elif ch == "$":
            out.append("&#36;")  # a pair of $ is math in Mintlify, and \$ renders the backslash
        elif ch == " ":
            out.append("&nbsp;")
        else:
            out.append(ch)
    return "".join(out)


def escape_line_start(text: str) -> str:
    """Escape Markdown block syntax at the start of a paragraph line."""
    if re.match(r"(#{1,6}|[-+*>]|=+|\d+[.)])(\s|$)", text):
        m = re.match(r"(\d+)([.)])", text)
        if m:
            return m.group(1) + "\\" + text[len(m.group(1)) :]
        return "\\" + text
    return text


def code_span(code: str) -> str:
    code = code.replace("\n", " ")
    if not code.strip():
        return "<code>" + escape_text(code).replace(" ", "&nbsp;") + "</code>" if code else ""
    runs = [len(r) for r in re.findall(r"`+", code)]
    ticks = "`" * (max(runs) + 1 if runs else 1)
    pad = " " if code.startswith("`") or code.endswith("`") or (code[0] == " " and code[-1] == " ") else ""
    return f"{ticks}{pad}{code}{pad}{ticks}"


def fence(code: str, lang: str = "", meta: str = "") -> str:
    runs = [len(r) for r in re.findall(r"^\s*(`{3,})", code, re.M)]
    ticks = "`" * max([3] + [r + 1 for r in runs])
    info = " ".join(x for x in (lang, meta) if x)
    return f"{ticks}{info}\n{code}\n{ticks}"


def guess_lang(code: str) -> str:
    s = code.lstrip()
    first = s.split("\n", 1)[0]
    if first.startswith("$ ") or first == "$":
        return "bash"
    if s.startswith("<"):
        return "xml"
    if s.startswith(("{", "[")):
        return "json"
    if re.match(r"(package |import |public |@Override)", s):
        return "java"
    if re.match(r"(schema|document|rank-profile|field|search|struct|function)\s+[\w-]+", s):
        return "js"  # no highlighter knows schemas; the branch uses js
    if re.match(r"select\s", s, re.I):
        return "sql"
    return "txt"


# ---------------------------------------------------------------------------
# HTML tree

VOID = frozenset("area base br col embed hr img input link meta source track wbr".split())
BLOCK = frozenset(
    "address article aside blockquote details dialog dd div dl dt fieldset figcaption figure footer form "
    "h1 h2 h3 h4 h5 h6 header hr li main nav ol p section table ul x-callout x-pre x-mathblock iframe object "
    "video summary".split()
)
DROP = frozenset("script style button noscript input select textarea".split())


@dataclass(eq=False)
class Node:
    tag: str
    attrs: dict[str, str] = field(default_factory=dict)
    children: list = field(default_factory=list)
    parent: Node | None = None


class TreeBuilder(HTMLParser):
    """HTML parser that closes elements the way browsers do when end tags are omitted."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Node("root")
        self.stack = [self.root]

    def _close_until(self, tags: set[str], boundary: set[str]) -> None:
        for i in range(len(self.stack) - 1, 0, -1):
            tag = self.stack[i].tag
            if tag in boundary:
                return
            if tag in tags:
                del self.stack[i:]
                return

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in BLOCK and tag != "li":
            self._close_until({"p"}, {"td", "th", "li", "x-callout", "div", "dd", "blockquote", "table"})
        if tag == "li":
            self._close_until({"li"}, {"ul", "ol"})
        elif tag in ("dt", "dd"):
            self._close_until({"dt", "dd"}, {"dl"})
        elif tag == "tr":
            self._close_until({"tr"}, {"table", "thead", "tbody", "tfoot"})
        elif tag in ("td", "th"):
            self._close_until({"td", "th"}, {"tr", "table"})
        elif tag in ("thead", "tbody", "tfoot"):
            self._close_until({"thead", "tbody", "tfoot"}, {"table"})
        node = Node(tag, {k: v or "" for k, v in attrs}, [], self.stack[-1])
        self.stack[-1].children.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag.lower() not in VOID and self.stack[-1].tag == tag.lower():
            self.stack.pop()

    def handle_endtag(self, tag):
        tag = tag.lower()
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                return
            if self.stack[i].tag in ("table", "td", "th") and tag not in ("table", "td", "th", "tr", "tbody", "thead"):
                return

    def handle_data(self, data):
        self.stack[-1].children.append(data)

    def handle_comment(self, data):
        self.stack[-1].children.append(Node("x-comment", {"text": data}, [], self.stack[-1]))


# ---------------------------------------------------------------------------
# Code and math extraction (before parsing, so their content is not parsed as HTML)


@dataclass
class Page:
    source: str  # repo path of the source page
    codes: list[tuple[str, str, str]] = field(default_factory=list)  # (lang, meta, code)
    maths: list[tuple[str, bool]] = field(default_factory=list)  # (latex, display)


PRE_RE = re.compile(r"<pre\b([^>]*)>(.*?)</pre>", re.DOTALL | re.IGNORECASE)
HILITE_RE = re.compile(r'<span\s+class="pre-hilite"\s*>(.*?)</span>', re.DOTALL | re.IGNORECASE)


def code_from_pre(inner: str) -> tuple[str, list[int]]:
    """Text of a <pre> body, and the 1-based lines marked with pre-hilite."""
    inner = inner.replace("\r\n", "\n")
    if inner.startswith("\n"):
        inner = inner[1:]
    marked = HILITE_RE.sub(lambda m: "" + m.group(1) + "", inner)
    text = html.unescape(re.sub(r"</?[a-zA-Z][^>]*>", "", marked))
    lines = text.rstrip().split("\n")
    hl = [i + 1 for i, line in enumerate(lines) if "" in line or "" in line]
    code = "\n".join(lines).replace("", "").replace("", "")
    return code, hl


def highlight_meta(lines: list[int]) -> str:
    if not lines:
        return ""
    ranges, start = [], lines[0]
    for prev, cur in zip(lines, lines[1:] + [None]):
        if cur != prev + 1:
            ranges.append(str(start) if start == prev else f"{start}-{prev}")
            start = cur
    return "highlight={" + ",".join(ranges) + "}"


def extract_code(body: str, page: Page) -> str:
    def add(lang: str, meta: str, code: str) -> str:
        page.codes.append((lang, meta, code))
        return f'<x-pre n="{len(page.codes) - 1}"></x-pre>'

    def highlight_repl(m: re.Match) -> str:
        lang, code = m.group(1), m.group(2)
        return add(lang or guess_lang(code), "", code)

    hl_re = re.compile(f"{HL_START}(.*?){HL_SEP}(.*?){HL_END}", re.DOTALL)
    # <pre>{% highlight %}...{% endhighlight %}</pre>: the pre is only a wrapper
    body = re.sub(r"<pre\b[^>]*>\s*(" + hl_re.pattern + r")\s*</pre>", lambda m: m.group(1), body, flags=re.DOTALL)
    body = hl_re.sub(highlight_repl, body)
    # Scripts may contain "<pre>" in strings; drop them before looking for <pre> elements.
    body = strip_dropped(body)

    def pre_repl(m: re.Match) -> str:
        attrs, inner = m.group(1), m.group(2)
        # js/process_pre.js labels file examples used by the documentation tests
        path = re.search(r'data-path="([^"]*)"', attrs) if 'data-test="file"' in attrs else None
        label = f"<p><code>Paste the above into file {html.escape(path.group(1))}</code></p>" if path else ""
        if re.search(r"display:\s*none", attrs):
            return label
        code, hl = code_from_pre(inner)
        return add(guess_lang(code), highlight_meta(hl), code) + label

    return PRE_RE.sub(pre_repl, body)


MATH_RE = re.compile(r"<math\b([^>]*)>(.*?)</math>", re.DOTALL | re.IGNORECASE)


def extract_math(body: str, page: Page) -> str:
    def repl(m: re.Match) -> str:
        display = 'display="block"' in m.group(1)
        page.maths.append((mathml_to_latex(m.group(0)), display))
        tag = "x-mathblock" if display else "x-math"
        return f'<{tag} n="{len(page.maths) - 1}"></{tag}>'

    return MATH_RE.sub(repl, body)


def strip_dropped(body: str) -> str:
    for tag in ("script", "style", "button", "noscript"):
        body = re.sub(rf"<{tag}\b.*?</{tag}>", "", body, flags=re.DOTALL | re.IGNORECASE)
    return body


# ---------------------------------------------------------------------------
# MathML -> LaTeX

MO = {
    "⋅": r"\cdot", "·": r"\cdot", "×": r"\times", "∑": r"\sum", "∏": r"\prod", "−": "-", "≤": r"\leq",
    "≥": r"\geq", "≠": r"\neq", "∞": r"\infty", "∈": r"\in", "→": r"\rightarrow", "←": r"\leftarrow",
    "√": r"\sqrt", "∫": r"\int", "∗": "*", "…": r"\ldots", "⋯": r"\cdots", "±": r"\pm", "∣": "|",
    "{": r"\{", "}": r"\}", "⁡": "", "⁢": "", "%": r"\%", "#": r"\#", "&": r"\&",
}
GREEK = {c: "\\" + n for c, n in zip("αβγδεζηθικλμνξπρστυφχψωΔΓΘΛΞΠΣΦΨΩ", (
    "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu nu xi pi rho sigma tau upsilon "
    "phi chi psi omega Delta Gamma Theta Lambda Xi Pi Sigma Phi Psi Omega").split())}


def mathml_to_latex(markup: str) -> str:
    b = TreeBuilder()
    b.feed(markup)
    b.close()
    math = next((c for c in b.root.children if isinstance(c, Node)), None)
    return re.sub(r"\s+", " ", ml(math)).strip() if math else ""


def ml_text(s: str) -> str:
    s = s.strip()
    return "".join(GREEK.get(c, MO.get(c, c)) for c in s)


def ml(node) -> str:
    if isinstance(node, str):
        return ml_text(node) if node.strip() else ""
    kids = [c for c in node.children if isinstance(c, Node) or c.strip()]
    tag = node.tag
    parts = [ml(c) for c in kids]
    if tag == "semantics":
        for c in kids:
            if isinstance(c, Node) and c.tag == "annotation" and "tex" in c.attrs.get("encoding", ""):
                return "".join(x for x in c.children if isinstance(x, str)).strip()
        return parts[0] if parts else ""
    if tag in ("annotation", "annotation-xml"):
        return ""
    if tag == "mi":
        text = "".join(x for x in node.children if isinstance(x, str)).strip()
        if len(text) > 1 and text not in GREEK and not text.startswith("\\"):
            return r"\text{" + text.replace("_", r"\_") + "}"
        return ml_text(text)
    if tag == "mtext":
        text = "".join(x for x in node.children if isinstance(x, str))
        return r"\text{" + text.replace("_", r"\_") + "}"
    if tag == "mspace":
        return r"\ "
    if tag == "mfrac" and len(parts) == 2:
        return r"\frac{" + parts[0] + "}{" + parts[1] + "}"
    if tag == "msqrt":
        return r"\sqrt{" + " ".join(parts) + "}"
    if tag == "mroot" and len(parts) == 2:
        return r"\sqrt[" + parts[1] + "]{" + parts[0] + "}"
    if tag in ("msub", "munder") and len(parts) == 2:
        return "{" + parts[0] + "}_{" + parts[1] + "}"
    if tag in ("msup", "mover") and len(parts) == 2:
        return "{" + parts[0] + "}^{" + parts[1] + "}"
    if tag in ("msubsup", "munderover") and len(parts) == 3:
        return "{" + parts[0] + "}_{" + parts[1] + "}^{" + parts[2] + "}"
    if tag == "mfenced":
        o, c = node.attrs.get("open", "("), node.attrs.get("close", ")")
        sep = node.attrs.get("separators", ",")
        o, c = MO.get(o, o) or ".", MO.get(c, c) or "."
        return r"\left" + o + " " + (sep[:1] + " ").join(parts) + r" \right" + c
    if tag == "mtable":
        return r"\begin{matrix} " + r" \\ ".join(parts) + r" \end{matrix}"
    if tag == "mtr":
        return " & ".join(parts)
    return " ".join(p for p in parts if p)


# ---------------------------------------------------------------------------
# HTML -> MDX rendering


def is_block(node) -> bool:
    return isinstance(node, Node) and (node.tag in BLOCK or node.tag in ("x-pre", "x-mathblock"))


def has_block(node: Node) -> bool:
    return any(is_block(c) or (isinstance(c, Node) and c.tag not in ("a",) and has_block(c)) for c in node.children)


# Jekyll ids are anchor targets. Mintlify drops them, and derives heading ids from the
# heading text, so ids that would be lost are kept as <a id="..." /> anchors.
NO_ANCHOR = frozenset("td th tr thead tbody tfoot li x-pre x-math x-mathblock".split())
BLOCK_ANCHOR = frozenset("p div dt dd dl ul ol blockquote figure section table details".split())


def anchor_id(n: Node) -> str:
    return n.attrs.get("id") or (n.attrs.get("name", "") if n.tag == "a" else "")


def anchor_tag(anchor: str) -> str:
    return f'<a id="{html.escape(anchor, quote=True)}" />'


def plain_text(n) -> str:
    if isinstance(n, str):
        return n
    return "".join(plain_text(c) for c in n.children if not (isinstance(c, Node) and c.tag in DROP))


def heading_slug(text: str) -> str:
    """The id Mintlify gives a heading (github-slugger)."""
    text = re.sub(r"\s+", " ", text).strip().lower()
    return re.sub(r"[^\w\- ]", "", text).replace(" ", "-")


class Renderer:
    def __init__(self, page: Page):
        self.page = page
        self.slugs: dict[str, int] = {}

    def unique_slug(self, text: str) -> str:
        base = heading_slug(text)
        n = self.slugs.get(base, 0)
        self.slugs[base] = n + 1
        return base if n == 0 else f"{base}-{n}"

    # -- inline ---------------------------------------------------------------

    def inline(self, nodes: list) -> str:
        text = "".join(self.inline_node(n) for n in nodes)
        text = re.sub(r"[ \t\n]+", " ", text)
        return text.strip()

    def inline_node(self, n) -> str:
        if isinstance(n, Node) and n.tag not in NO_ANCHOR and anchor_id(n) and n.tag not in DROP:
            return anchor_tag(anchor_id(n)) + self.inline_content(n)
        return self.inline_content(n)

    def inline_content(self, n) -> str:
        if isinstance(n, str):
            return escape_text(re.sub(r"\s+", " ", n))
        tag = n.tag
        if tag in DROP or tag == "x-comment":
            return ""
        if tag == "br":
            return "<br/>"
        if tag in ("code", "tt", "kbd"):
            if any(isinstance(c, Node) for c in n.children):
                return "<code>" + self.inline(n.children) + "</code>"
            return code_span(re.sub(r"\s+", " ", "".join(n.children)))
        if tag in ("em", "i", "strong", "b"):
            inner = "".join(self.inline_node(c) for c in n.children)
            return self.emphasis(inner, "**" if tag in ("strong", "b") else "*", tag in ("strong", "b"))
        if tag == "a":
            inner = self.inline(n.children)
            href = n.attrs.get("href")
            if href is None or not inner:
                return inner
            href = convert_href(href, self.page.source)
            return f"[{inner}]({md_link_target(href)})"
        if tag == "img":
            return self.image(n, inline=True)
        if tag in ("sub", "sup", "s", "u", "mark", "small", "del", "ins"):
            return f"<{tag}>{self.inline(n.children)}</{tag}>"
        if tag == "x-math":
            return "$" + self.page.maths[int(n.attrs["n"])][0] + "$"
        if tag == "x-version":
            return code_span("".join(c for c in n.children if isinstance(c, str)))
        if tag == "x-chip":
            label, tip = CHIPS[n.attrs["name"]]
            return f'<Tooltip tip="{tip}">**{label}**</Tooltip>'
        if tag == "x-pre":
            lang, meta, code = self.page.codes[int(n.attrs["n"])]
            return code_span(code) if "\n" not in code else code_span(code)
        return "".join(self.inline_node(c) for c in n.children)

    @staticmethod
    def emphasis(inner: str, marker: str, strong: bool) -> str:
        lead = inner[: len(inner) - len(inner.lstrip())]
        trail = inner[len(inner.rstrip()) :]
        core = inner.strip()
        if not core:
            return inner
        # Placeholders: finish_emphasis() decides between Markdown markers and HTML tags
        # once the surrounding characters are known.
        return f"{lead}{marker}{core}{marker}{trail}"

    def image(self, n: Node, inline: bool) -> str:
        src = convert_href(n.attrs.get("src", ""), self.page.source)
        alt = n.attrs.get("alt", "").replace("[", "").replace("]", "")
        return f"![{alt}]({md_link_target(src)})"

    # -- blocks -----------------------------------------------------------------

    def blocks(self, nodes: list) -> list[str]:
        out: list[str] = []
        run: list = []

        def flush():
            if run:
                para = self.paragraph(run)
                if para:
                    out.append(para)
                run.clear()

        for n in nodes:
            if is_block(n) or (isinstance(n, Node) and n.tag in ("x-comment",)):
                flush()
                if n.tag in BLOCK_ANCHOR and anchor_id(n):
                    out.append(anchor_tag(anchor_id(n)))
                out.extend(self.block(n))
            elif isinstance(n, Node) and n.tag not in ("a",) and n.tag not in DROP and has_block(n):
                flush()
                out.extend(self.blocks(n.children))  # e.g. <span> wrapping blocks
            else:
                run.append(n)
        flush()
        return [b for b in out if b.strip()]

    def paragraph(self, nodes: list) -> str:
        imgs = [n for n in nodes if isinstance(n, Node) and n.tag == "img"]
        rest = [n for n in nodes if not (isinstance(n, str) and not n.strip()) and n not in imgs]
        if len(imgs) == 1 and not rest:
            return "<Frame>\n" + self.image(imgs[0], inline=False) + "\n</Frame>"
        text = self.inline(nodes)
        text = re.sub(r"(<br/>\s*)+$", "", text)
        return finish_emphasis(escape_line_start(text)) if text else ""

    def block(self, n: Node) -> list[str]:
        tag = n.tag
        if tag == "x-comment":
            text = n.attrs["text"].strip().replace("*/", "* /")
            return ["{/* " + text + " */}"] if text else []
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            text = finish_emphasis(self.inline(n.children))
            if not text:
                return [anchor_tag(anchor_id(n))] if anchor_id(n) else []
            heading = f"{'#' * int(tag[1])} {text}"
            slug = self.unique_slug(plain_text(n))
            if anchor_id(n) and anchor_id(n) != slug:
                return [anchor_tag(anchor_id(n)) + "\n" + heading]
            return [heading]
        if tag == "p" or tag in ("figcaption", "summary"):
            return self.blocks(n.children)
        if tag == "x-pre":
            lang, meta, code = self.page.codes[int(n.attrs["n"])]
            return [fence(code, lang, meta)]
        if tag == "x-mathblock":
            return ["$$\n" + self.page.maths[int(n.attrs["n"])][0] + "\n$$"]
        if tag in ("ul", "ol"):
            return [self.list_block(n)]
        if tag == "dl":
            return self.definition_list(n)
        if tag in ("dt", "dd", "li"):
            return self.blocks(n.children)
        if tag == "table":
            return [self.table(n)]
        if tag == "blockquote":
            inner = "\n\n".join(self.blocks(n.children))
            return ["\n".join("> " + line if line else ">" for line in inner.split("\n"))]
        if tag == "hr":
            return ["---"]
        if tag == "x-callout":
            component, label = CALLOUT_KINDS[n.attrs["kind"]]
            inner = "\n\n".join(self.blocks(n.children))
            return [f"<{component}>\n**{label}:**\n\n{inner}\n</{component}>"]
        if tag == "div":
            cls = n.attrs.get("class", "")
            m = re.search(r"vespa-notification-(\w+)", cls)
            if m and m.group(1) in ("note", "important", "warning", "prereqs"):
                component = {"note": "Note", "prereqs": "Note", "important": "Warning", "warning": "Warning"}[m.group(1)]
                inner = "\n\n".join(self.blocks(n.children))
                return [f"<{component}>\n{inner}\n</{component}>"]
            return self.blocks(n.children)
        if tag == "figure":
            img = find(n, "img")
            cap = find(n, "figcaption")
            if img is None:
                return self.blocks(n.children)
            caption = self.inline(cap.children) if cap else ""
            attr = f' caption="{html.escape(caption, quote=True)}"' if caption else ""
            return [f"<Frame{attr}>\n{self.image(img, inline=False)}\n</Frame>"]
        if tag == "details":
            summary = find(n, "summary")
            title = self.inline(summary.children) if summary else "Details"
            rest = [c for c in n.children if c is not summary]
            inner = "\n\n".join(self.blocks(rest))
            return [f'<Accordion title="{html.escape(title, quote=True)}">\n\n{inner}\n\n</Accordion>']
        if tag in ("iframe", "object", "video"):
            # Embedded content stays HTML; an SVG in <object> keeps its links clickable, unlike <img>
            attrs = jsx_attrs(n.attrs, ("src", "data", "type", "width", "height", "title", "allow",
                                        "allowfullscreen", "frameborder", "controls", "poster", "style"))
            fallback = self.inline(n.children)
            return [f"<{tag}{attrs}>" + (f"\n  {finish_emphasis(fallback)}\n" if fallback else "") + f"</{tag}>"]
        return self.blocks(n.children)

    def list_block(self, n: Node) -> str:
        ordered = n.tag == "ol"
        start = int(n.attrs.get("start", "1") or 1) if ordered else 1
        items = [c for c in n.children if isinstance(c, Node) and c.tag == "li"]
        # stray content between <li> elements belongs to the previous item
        rendered = []
        item_blocks = [self.blocks(li.children) or [""] for li in items]
        for li, blocks in zip(items, item_blocks):
            if anchor_id(li):
                if is_paragraph(blocks[0]) and blocks[0]:
                    blocks[0] = anchor_tag(anchor_id(li)) + " " + blocks[0]
                else:
                    blocks.insert(0, anchor_tag(anchor_id(li)))
        # Loose (blank lines between items) only when an item has several paragraphs;
        # text followed by a nested list or code keeps the list tight.
        loose = any(sum(1 for b in blocks if is_paragraph(b)) > 1 for blocks in item_blocks)
        for i, blocks in enumerate(item_blocks):
            marker = f"{start + i}. " if ordered else "- "
            pad = " " * len(marker)
            body = blocks[0]
            for prev, b in zip(blocks, blocks[1:]):
                tight = not loose and (is_list(b) or b.startswith("```")) and not prev.startswith("<")
                body += ("\n" if tight else "\n\n") + b
            lines = body.split("\n")
            text = marker + lines[0] + "".join("\n" + (pad + line if line else "") for line in lines[1:])
            rendered.append(text.rstrip())
        if "howto" in n.attrs.get("class", "") and ordered:
            steps = []
            for li in items:
                inner = "\n\n".join(self.blocks(li.children))
                steps.append("<Step>\n" + inner + "\n</Step>")
            return "<Steps>\n" + "\n".join(steps) + "\n</Steps>"
        return ("\n\n" if loose else "\n").join(rendered)

    def definition_list(self, n: Node) -> list[str]:
        out = []
        for c in n.children:
            if isinstance(c, Node) and c.tag == "dt":
                text = finish_emphasis(self.inline(c.children))
                out.append(f"**{text}**" if text and "**" not in text else text)
            elif isinstance(c, Node) and c.tag == "dd":
                out.extend(self.blocks(c.children))
        return out

    def table(self, n: Node) -> str:
        rows: list[tuple[str, Node]] = []  # (section, tr)

        def collect(node: Node, section: str):
            for c in node.children:
                if not isinstance(c, Node):
                    continue
                if c.tag == "tr":
                    rows.append((section, c))
                elif c.tag in ("thead", "tbody", "tfoot"):
                    collect(c, c.tag)
                elif c.tag in ("caption", "colgroup", "col"):
                    continue
                else:
                    collect(c, section)

        collect(n, "tbody")
        if rows and rows[0][0] == "tbody":
            first_cells = [c for c in rows[0][1].children if isinstance(c, Node) and c.tag in ("td", "th")]
            if first_cells and all(c.tag == "th" for c in first_cells):
                rows[0] = ("thead", rows[0][1])
        lines = ['<table className="vespa-table">']
        caption = next((c for c in n.children if isinstance(c, Node) and c.tag == "caption"), None)
        if caption is not None and self.inline(caption.children):
            lines.append(f"  <caption>{finish_emphasis(self.inline(caption.children))}</caption>")
        for section in ("thead", "tbody", "tfoot"):
            sec_rows = [tr for s, tr in rows if s == section]
            if not sec_rows:
                continue
            lines.append(f"  <{section}>")
            for tr in sec_rows:
                lines.append("    <tr" + cell_attrs(tr) + ">")
                for cell in tr.children:
                    if isinstance(cell, Node) and cell.tag in ("td", "th"):
                        lines.append(self.cell(cell))
                lines.append("    </tr>")
            lines.append(f"  </{section}>")
        lines.append("</table>")
        return "\n".join(lines)

    def cell(self, c: Node) -> str:
        open_tag = f"      <{c.tag}{cell_attrs(c)}>"
        if cell_has_blocks(c):
            inner = "\n\n".join(self.blocks(c.children))
            # the closing tag starts the line, or it would continue a list at the end of the cell
            return f"{open_tag}\n\n{inner}\n\n</{c.tag}>"
        text = finish_emphasis(self.inline(c.children))
        return f"{open_tag}{text}</{c.tag}>"


def cell_has_blocks(c: Node) -> bool:
    """Whether a table cell needs Markdown blocks; a single paragraph stays inline."""
    paragraphs = [n for n in c.children if isinstance(n, Node) and n.tag == "p"]
    others = [n for n in c.children if n not in paragraphs and not (isinstance(n, str) and not n.strip())]
    if len(paragraphs) == 1 and not others:
        return has_block(paragraphs[0])
    return has_block(c)


def is_list(block: str) -> bool:
    return bool(re.match(r"(- |\d+\. )", block))


def is_paragraph(block: str) -> bool:
    return not (is_list(block) or block.startswith(("```", "<", "$$", "#", "{/*", ">")))


def find(n: Node, tag: str) -> Node | None:
    for c in n.children:
        if isinstance(c, Node):
            if c.tag == tag:
                return c
            r = find(c, tag)
            if r:
                return r
    return None


def jsx_attr(name: str) -> str:
    return {"class": "className", "colspan": "colSpan", "rowspan": "rowSpan", "allowfullscreen": "allowFullScreen",
            "frameborder": "frameBorder"}.get(name, name)


def jsx_style(css: str) -> str:
    """CSS declarations -> a JSX style object, e.g. max-width:600px -> {{maxWidth: "600px"}}"""
    props = []
    for decl in css.split(";"):
        name, sep, value = decl.partition(":")
        if sep and name.strip() and value.strip():
            key = re.sub(r"-(\w)", lambda m: m.group(1).upper(), name.strip().lower())
            props.append(f"{key}: {json_str(value.strip())}")
    return "{{" + ", ".join(props) + "}}"


def json_str(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def jsx_attrs(attrs: dict[str, str], allowed: tuple[str, ...]) -> str:
    out = []
    for k, v in attrs.items():
        if k not in allowed:
            continue
        if k == "style":
            if jsx_style(v) != "{{}}":
                out.append(f"style={jsx_style(v)}")
        elif k in ("allowfullscreen", "controls") and not v:
            out.append(jsx_attr(k))
        else:
            out.append(f'{jsx_attr(k)}="{html.escape(v, quote=True)}"')
    return (" " + " ".join(out)) if out else ""


def cell_attrs(n: Node) -> str:
    out = []
    for k, v in n.attrs.items():
        if k in ("colspan", "rowspan") and v.strip().isdigit():
            out.append(f'{jsx_attr(k)}="{v.strip()}"')
        elif k == "id" and v:
            out.append(f'id="{html.escape(v, quote=True)}"')
        elif k == "class" and re.search(r"\btd-\w+", v):
            out.append(f'className="{" ".join(re.findall(r"td-[\w-]+", v))}"')
    return (" " + " ".join(out)) if out else ""


def finish_emphasis(text: str) -> str:
    """Resolve emphasis placeholders: Markdown markers where they flank, HTML tags otherwise."""

    pattern = re.compile("(\\*{1,2})((?:(?!\\1).)*?)\\1", re.DOTALL)
    while True:
        m = pattern.search(text)
        if not m:
            break
        marker, core = m.group(1), m.group(2)
        plain = core.replace("", "").replace("", "")
        before = text[m.start() - 1] if m.start() else " "
        after = text[m.end()] if m.end() < len(text) else " "
        first, last = plain[:1] or " ", plain[-1:] or " "
        # CommonMark flanking rules for the opening and closing delimiter runs
        opens = not first.isspace() and (not is_punct(first) or before.isspace() or is_punct(before))
        closes = not last.isspace() and (not is_punct(last) or after.isspace() or is_punct(after))
        # A backslash escape right before the closer would escape it
        ok = opens and closes and not core.endswith("\\") and before != "\\" and "*" not in (before, after)
        tag = "strong" if len(marker) == 2 else "em"
        if ok and marker == "*" and not (before.isalnum() or after.isalnum() or "_" in (before, after)):
            marker = "_"
        rep = f"{marker}{core}{marker}" if ok else f"<{tag}>{core}</{tag}>"
        text = text[: m.start()] + rep + text[m.end() :]
    return text.replace("", "").replace("", "")


def is_punct(ch: str) -> bool:
    import unicodedata

    return unicodedata.category(ch)[0] in "PS"


def html_to_mdx(body: str, page: Page) -> str:
    body = extract_code(body, page)
    body = extract_math(body, page)
    body = strip_dropped(body)
    builder = TreeBuilder()
    builder.feed(body)
    builder.close()
    blocks = Renderer(page).blocks(builder.root.children)
    return "\n\n".join(blocks)


# ---------------------------------------------------------------------------
# Markdown (kramdown) -> MDX

HTML_BLOCK_START = re.compile(
    r"^(\s*)<(div|pre|table|p|ul|ol|dl|h[1-6]|figure|blockquote|details|iframe|object|video|img|section|script|style|button|math|hr|br|x-callout|x-chip)\b",
    re.IGNORECASE,
)
FENCE_RE = re.compile(r"^(\s*)(`{3,}|~{3,})(.*)$")
LIST_ITEM_RE = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+")
INLINE_TAG_RE = re.compile(r"<(/?)([a-zA-Z][\w-]*)((?:\s+[^<>]*?)?)(/?)>")
KNOWN_INLINE = frozenset("a b i em strong code br img sub sup span kbd s u mark small del ins tt x-version x-chip".split())
MDX_COMPONENTS = frozenset("Note Warning Danger Info Tip Tooltip Frame Steps Step Accordion".split())


def markdown_to_mdx(body: str, page: Page) -> str:
    lines = body.replace("\r\n", "\n").split("\n")
    out: list[str] = []
    prose: set[int] = set()  # indexes in out of Markdown prose lines
    i = 0
    in_list = False
    while i < len(lines):
        line = lines[i]
        # highlight blocks rendered by Liquid
        if HL_START in line:
            j = i
            chunk = line
            while HL_END not in chunk and j + 1 < len(lines):
                j += 1
                chunk += "\n" + lines[j]
            indent = re.match(r"\s*", line).group(0)
            m = re.search(f"{HL_START}(.*?){HL_SEP}(.*?){HL_END}", chunk, re.DOTALL)
            if m:
                before, after = chunk[: m.start()].strip(), chunk[m.end() :].strip()
                if before:
                    out.append(indent + md_inline(before, page))
                code = m.group(2)
                out.append(indent_block(fence(code, m.group(1) or guess_lang(code)), indent))
                if after:
                    out.append(indent + md_inline(after, page))
            i = j + 1
            continue
        m = FENCE_RE.match(line)
        if m:
            indent, ticks, info = m.groups()
            j = i + 1
            while j < len(lines) and not re.match(rf"^\s*{re.escape(ticks[0])}{{{len(ticks)},}}\s*$", lines[j]):
                j += 1
            info = info.strip() or guess_lang("\n".join(l[len(indent):] for l in lines[i + 1 : j]))
            out.append(f"{indent}{ticks}{info}")
            # kramdown keeps less-indented code lines in a list item's fence; CommonMark would end the item
            code = lines[i + 1 : j]
            if indent and any(l.strip() and not l.startswith(indent) for l in code):
                code = [indent + l if l.strip() else l for l in code]
            out.extend(code)
            out.append(f"{indent}{ticks}")
            i = j + 1
            continue
        stripped = line.strip()
        if stripped.startswith("<!--"):
            j = i
            chunk = line
            while "-->" not in chunk and j + 1 < len(lines):
                j += 1
                chunk += "\n" + lines[j]
            comment, _, rest = chunk.partition("-->")
            text = comment.strip()[4:].strip().replace("*/", "* /")
            if text:
                out.append("{/* " + text + " */}")
            if rest.strip():
                out.append(md_inline(rest.strip(), page))
            i = j + 1
            continue
        if re.match(r"^\{:.*\}\s*$", stripped) or stripped in ("* TOC", "{:toc}"):
            # {: #id } gives the preceding block (e.g. a heading) an id; keep it as an anchor
            m = re.search(r"#([\w-]+)", stripped)
            if m:
                prev = next((k for k in range(len(out) - 1, -1, -1) if out[k].strip()), None)
                anchor = anchor_tag(m.group(1))
                if prev is not None and re.match(r"\s*#{1,6} ", out[prev]):
                    out.insert(prev, anchor)
                else:
                    out.append(anchor)
            i += 1
            continue
        m = HTML_BLOCK_START.match(line)
        if m and not (m.group(2).lower() in ("img", "br") and not re.match(r"^\s*<(img|br)\b[^>]*>\s*$", line)):
            indent = m.group(1)
            j = html_block_end(lines, i, m.group(2).lower())
            chunk = "\n".join(lines[i : j + 1])
            converted = html_to_mdx(chunk, page)
            if converted:
                out.append("")
                out.append(indent_block(converted, indent))
                out.append("")
            i = j + 1
            continue
        # indented code block (not a list continuation)
        if re.match(r"^( {4}|\t)\S", line) and not in_list and (not out or not out[-1].strip()):
            j = i
            block = []
            while j < len(lines) and (re.match(r"^( {4}|\t)", lines[j]) or not lines[j].strip()):
                block.append(re.sub(r"^( {4}|\t)", "", lines[j]))
                j += 1
            while block and not block[-1].strip():
                block.pop()
                j -= 1
            code = "\n".join(block)
            out.append(fence(code, guess_lang(code)))
            i = j
            continue
        if stripped.startswith("|") and i + 1 < len(lines) and TABLE_SEP_RE.match(lines[i + 1].strip()):
            j = i
            while j < len(lines) and lines[j].strip().startswith("|"):
                j += 1
            out.append("")
            out.append(gfm_table(lines[i:j], page))
            out.append("")
            i = j
            continue
        if LIST_ITEM_RE.match(line):
            in_list = True
        elif stripped and not line.startswith((" ", "\t")):
            in_list = False
        converted = md_line(line, page) if stripped else ""
        if converted and prose_continues(out, prose, stripped):
            out[-1] = out[-1].rstrip() + " " + converted.strip()
        else:
            out.append(converted)
            prose.add(len(out) - 1) if converted and not BLOCK_LINE_RE.match(stripped) else None
        i += 1
    text = "\n".join(out)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


TABLE_SEP_RE = re.compile(r"^\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)*\|?$")
BLOCK_LINE_RE = re.compile(r"^(#{1,6}\s|[-*+]\s|\d+[.)]\s|>|\||```|~~~|<|\{/\*|\$\$|(-{3,}|\*{3,}|_{3,}|={3,})\s*$)")


def prose_continues(out: list[str], prose: set[int], stripped: str) -> bool:
    """Whether a source line continues the previous paragraph line (soft line break)."""
    if not out or len(out) - 1 not in prose or not out[-1].strip():
        return False
    prev = out[-1]
    if prev.endswith(("  ", "\\", "<br/>")):
        return False
    return not BLOCK_LINE_RE.match(stripped)


def gfm_table(rows: list[str], page: Page) -> str:
    def cells(row: str) -> list[str]:
        row = row.strip()
        row = row[1:] if row.startswith("|") else row
        row = row[:-1] if row.endswith("|") and not row.endswith("\\|") else row
        parts, cur, in_code = [], "", False
        k = 0
        while k < len(row):
            ch = row[k]
            if ch == "\\" and k + 1 < len(row) and row[k + 1] == "|":
                cur += "|"
                k += 2
                continue
            if ch == "`":
                in_code = not in_code
            if ch == "|" and not in_code:
                parts.append(cur.strip())
                cur = ""
            else:
                cur += ch
            k += 1
        parts.append(cur.strip())
        return parts

    head, body = cells(rows[0]), [cells(r) for r in rows[2:]]
    lines = ['<table className="vespa-table">', "  <thead>", "    <tr>"]
    lines += [f"      <th>{md_inline(c, page)}</th>" for c in head]
    lines += ["    </tr>", "  </thead>", "  <tbody>"]
    for r in body:
        lines.append("    <tr>")
        lines += [f"      <td>{md_inline(c, page)}</td>" for c in r]
        lines.append("    </tr>")
    lines += ["  </tbody>", "</table>"]
    return "\n".join(lines)


def indent_block(text: str, indent: str) -> str:
    return "\n".join(indent + line if line else "" for line in text.split("\n"))


def html_block_end(lines: list[str], start: int, tag: str) -> int:
    """Index of the line that closes the HTML element opened on lines[start]; tags may span lines."""
    text = "\n".join(lines[start:])
    depth = 0
    for m in re.finditer(rf"<{tag}\b[^>]*?(/?)>|</{tag}\s*>", text, re.IGNORECASE):
        if m.group(0).startswith("</"):
            depth -= 1
        elif not m.group(1) and tag not in VOID:
            depth += 1
        if depth <= 0:
            return start + text.count("\n", 0, m.end())
    return len(lines) - 1


def md_line(line: str, page: Page) -> str:
    indent = re.match(r"\s*", line).group(0)
    return indent + md_inline(line[len(indent) :], page)


def md_inline(text: str, page: Page) -> str:
    """Make one line of kramdown Markdown valid MDX, leaving code spans alone."""
    parts = re.split(r"(`+)", text)
    out, i = [], 0
    while i < len(parts):
        part = parts[i]
        if part.startswith("`"):
            # find the matching closing run
            for j in range(i + 1, len(parts)):
                if parts[j] == part:
                    out.append("".join(parts[i : j + 1]))
                    i = j + 1
                    break
            else:
                out.append("\\`" * len(part))
                i += 1
            continue
        out.append(md_prose(part, page))
        i += 1
    return "".join(out)


def md_prose(text: str, page: Page) -> str:
    text = re.sub(r"\{:[^}]*\}", "", text)  # kramdown inline attribute lists
    text = re.sub(r"<(https?://[^>\s]+)>", r"[\1](\1)", text)
    # kramdown math is $$...$$; \(...\) is LaTeX inline math. Both become Mintlify math.
    pieces = re.split(r"(\$\$.+?\$\$|\\\(.+?\\\))", text)
    for k in range(len(pieces)):
        if k % 2 == 0:
            pieces[k] = md_prose_plain(pieces[k], page).replace("$", "&#36;")
        elif pieces[k].startswith("\\("):
            pieces[k] = "$" + pieces[k][2:-2] + "$"
    return "".join(pieces)


def md_prose_plain(text: str, page: Page) -> str:
    out = []
    pos = 0
    for m in INLINE_TAG_RE.finditer(text):
        out.append(escape_md_residue(text[pos : m.start()]))
        out.append(convert_inline_tag(m, page))
        pos = m.end()
    out.append(escape_md_residue(text[pos:]))
    result = "".join(out)
    # links: [text](target)
    result = re.sub(
        r"(!?\[[^\]]*\])\(((?:[^()\s]|\([^()\s]*\))+)((?:\s+\"[^\"]*\")?)\)",
        lambda m: f"{m.group(1)}({md_link_target(convert_href(m.group(2), page.source))}{m.group(3)})",
        result,
    )
    result = re.sub(r"^(\[[^\]]+\]):\s*(\S+)", lambda m: f"{m.group(1)}: {convert_href(m.group(2), page.source)}", result)
    return result


def escape_md_residue(text: str) -> str:
    """Escape what MDX treats specially but kramdown does not: braces and stray angle brackets."""
    text = re.sub(r"(?<!\\)([{}])", r"\\\1", text)
    return text.replace("<", "&lt;")


def convert_inline_tag(m: re.Match, page: Page) -> str:
    closing, tag, attrs, selfclose = m.groups()
    if tag in MDX_COMPONENTS:
        return m.group(0)
    t = tag.lower()
    if t not in KNOWN_INLINE:
        return escape_md_residue(m.group(0).replace("<", "&lt;"))
    if t == "br":
        return "<br/>"
    if t == "img":
        src = re.search(r'src="([^"]*)"', attrs)
        alt = re.search(r'alt="([^"]*)"', attrs)
        return f"![{alt.group(1) if alt else ''}]({convert_href(src.group(1), page.source) if src else ''})"
    if t == "a" and not closing:
        href = re.search(r'href="([^"]*)"', attrs)
        return f'<a href="{convert_href(href.group(1), page.source)}">' if href else "<a>"
    if t == "span":
        return ""
    if t == "x-chip" and not closing:
        name = re.search(r'name="([^"]*)"', attrs)
        label, tip = CHIPS.get(name.group(1) if name else "", ("", ""))
        return f'<Tooltip tip="{tip}">**{label}**</Tooltip>'
    if t in ("x-chip",):
        return ""
    return f"<{closing}{t}{'/' if selfclose and t in VOID else ''}>"


# ---------------------------------------------------------------------------
# Pages


def split_frontmatter(text: str) -> tuple[dict[str, object], str]:
    text = text.lstrip("﻿")
    m = re.match(r"---\n(.*?)\n---[ \t]*\n?", text, re.DOTALL)
    if not m:
        return {}, text
    meta: dict[str, object] = {}
    key = None
    for line in m.group(1).splitlines():
        if line.startswith("#") or not line.strip():
            continue
        if line.startswith((" ", "-")) and key:
            item = line.strip().lstrip("-").strip()
            if isinstance(meta.get(key), list):
                meta[key].append(item)
            continue
        k, _, v = line.partition(":")
        key = k.strip()
        v = v.strip()
        meta[key] = [] if not v else v.strip("\"'")
    return meta, text[m.end() :]


def outside_fences(text: str):
    """Yield (index, line, in_fence) for the lines of text."""
    fence_marker = None
    for i, line in enumerate(text.split("\n")):
        m = re.match(r"\s*(`{3,}|~{3,})", line)
        if m:
            if fence_marker is None:
                fence_marker = m.group(1)
                yield i, line, True
                continue
            if m.group(1)[0] == fence_marker[0] and len(m.group(1)) >= len(fence_marker) and not line.strip()[len(m.group(1)):].strip():
                fence_marker = None
                yield i, line, True
                continue
        yield i, line, fence_marker is not None


def demote_headings(mdx: str) -> str:
    """Mintlify renders the title as the page's h1, so body headings start at h2."""
    lines = mdx.split("\n")
    if not any(not f and line.startswith("# ") for _, line, f in outside_fences(mdx)):
        return mdx
    for i, line, in_fence in outside_fences(mdx):
        if not in_fence and re.match(r"#{1,5} ", line):
            lines[i] = "#" + line
    return "\n".join(lines)


def yaml_str(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def convert(source_text: str, path: Path | str) -> str:
    """Convert a Jekyll page to MDX. `path` is the page's path in the repository."""
    path = Path(path)
    source = str(path.relative_to(ROOT)) if path.is_absolute() else str(path)
    meta, body = split_frontmatter(source_text)
    # Some generated pages repeat their frontmatter block.
    while True:
        extra, rest = split_frontmatter(body.lstrip("\n"))
        if not extra:
            break
        body = rest
    is_md = source.endswith(".md")
    if str(meta.get("render_with_liquid", "")).lower() != "false":
        body = liquid(body, LiquidOptions(markdown=is_md))
    page = Page(source)
    mdx = markdown_to_mdx(body, page) if is_md else html_to_mdx(body, page)
    mdx = demote_headings(mdx)

    title = str(meta.get("title") or path.stem.replace("-", " ").title())
    fm = [f"title: {yaml_str(title)}"]
    slug = re.sub(r"(/index)?\.(html|md)$", "", source)
    side = sidebar_names().get(slug)
    if side and side != title:
        fm.append(f"sidebarTitle: {yaml_str(side)}")
    return "---\n" + "\n".join(fm) + "\n---\n\n" + mdx.strip() + "\n"


def keep_frontmatter(mdx: str, existing: str, keys: list[str]) -> str:
    """Copy frontmatter lines for `keys` from an existing page into converted MDX that lacks them."""
    old = re.match(r"---\n(.*?)\n---\n", existing, re.DOTALL)
    new = re.match(r"---\n(.*?)\n---\n", mdx, re.DOTALL)
    if not old or not new:
        return mdx
    have = {line.partition(":")[0] for line in new.group(1).splitlines()}
    extra = [line for line in old.group(1).splitlines() if line.partition(":")[0] in keys and line.partition(":")[0] not in have]
    if not extra:
        return mdx
    return "---\n" + new.group(1) + "\n" + "\n".join(extra) + "\n---\n" + mdx[new.end():]


def main() -> int:
    global REF
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("sources", nargs="+", help="source pages, e.g. en/applications/bundles.html")
    parser.add_argument("--ref", default=REF, help=f"git ref holding the Jekyll sources (default: {REF})")
    parser.add_argument("--stdout", action="store_true", help="print instead of writing .mdx files")
    parser.add_argument("--keep", default="description",
                        help="frontmatter keys kept from an existing .mdx file when the converter does not "
                             "set them (default: description)")
    args = parser.parse_args()
    REF = args.ref
    for source in args.sources:
        text = ref_file(source)
        if text is None:
            print(f"{source}: not found in {REF}", file=sys.stderr)
            continue
        mdx = convert(text, source)
        if args.stdout:
            sys.stdout.write(mdx)
        else:
            out = ROOT / re.sub(r"\.(html|md)$", ".mdx", source)
            if out.exists():
                mdx = keep_frontmatter(mdx, out.read_text(encoding="utf-8-sig"), args.keep.split(","))
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(mdx, encoding="utf-8")
            print(f"{source} -> {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
