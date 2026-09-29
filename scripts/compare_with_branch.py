#!/usr/bin/env python3
"""Compare converter output against the MDX pages on this branch.

For each Jekyll source page on the master ref (en/**/*.html, en/**/*.md) that has
not changed since --since, convert it and compare the result to the corresponding
.mdx file in the working tree. The branch pages were converted and then fixed by
hand, so a page that converts to the same MDX needs no manual fixes.

Differences are reported at two levels:

- lines: similarity of the MDX after whitespace normalization, i.e. markup and
  formatting differences.
- text: words present on only one side after stripping markup. "branch-only"
  text is usually something the converter drops or garbles; "converted-only"
  text is either converter noise or content the branch lost in the migration.

Usage:
    scripts/compare_with_branch.py                      # all unchanged pages
    scripts/compare_with_branch.py en/applications      # pages under a path
    scripts/compare_with_branch.py --diff-dir /tmp/out  # write per-page diffs
    scripts/compare_with_branch.py --converter mymodule:convert
"""

from __future__ import annotations

import argparse
import difflib
import html
import importlib
import json
import re
import subprocess
import sys
import os
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

DEFAULT_CONVERTER = "compare_with_branch:baseline_convert"


def baseline_convert(source: str, path: Path) -> str:
    """The existing scripts: html_to_mdx followed by fix_mdx_parse_errors."""
    from fix_mdx_parse_errors import fix_text
    from html_to_mdx import convert_text

    return fix_text(convert_text(source, path))


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout


def last_modified(ref: str) -> dict[str, str]:
    """Map each en/ source path on ref to the date (YYYY-MM-DD) of its last change."""
    out = git("log", "--format=%x00%cs", "--name-only", ref, "--", "en")
    dates: dict[str, str] = {}
    for entry in out.split("\0")[1:]:
        lines = entry.strip("\n").split("\n")
        for name in lines[1:]:
            if name:
                dates.setdefault(name, lines[0])
    return dates


def branch_target(source: str) -> Path | None:
    base = re.sub(r"\.(html|md)$", "", source)
    for candidate in (f"{base}.mdx", f"{base}/index.mdx"):
        if (ROOT / candidate).is_file():
            return ROOT / candidate
    return None


def is_redirect_stub(text: str) -> bool:
    m = re.match(r"---\n(.*?)\n---", text, re.DOTALL)
    return bool(m and re.search(r"^redirect_to:", m.group(1), re.M))


def split_frontmatter(text: str) -> tuple[dict[str, str], str]:
    m = re.match(r"---\n(.*?)\n---\n?", text, re.DOTALL)
    if not m:
        return {}, text
    meta = {}
    for line in m.group(1).splitlines():
        key, sep, val = line.partition(":")
        if sep and not line.startswith(("#", " ", "-")):
            meta[key.strip()] = val.strip().strip("\"'")
    return meta, text[m.end():]


def normalize_lines(body: str) -> list[str]:
    lines = [line.rstrip() for line in body.replace("\r\n", "\n").split("\n")]
    out: list[str] = []
    for line in lines:
        if line or (out and out[-1]):
            out.append(line)
    while out and not out[-1]:
        out.pop()
    return out


def words(body: str) -> list[str]:
    text = re.sub(r"\{/\*.*?\*/\}", " ", body, flags=re.DOTALL)  # MDX comments
    text = re.sub(r"</?[A-Za-z][^<>\n]*>", " ", text)  # tags, not a < in code such as tensor<float>
    text = re.sub(r"\]\([^)]*\)", "] ", text)  # link targets
    for _ in range(2):
        text = html.unescape(text)
    text = text.replace("{`", " ").replace("`}", " ")
    return re.findall(r"[A-Za-z0-9]+(?:[.'_-][A-Za-z0-9]+)*", text.lower())


def only_in(a: list[str], b: list[str], min_run: int) -> tuple[list[str], list[str]]:
    """Runs of at least min_run words present only in a, and only in b."""
    only_a, only_b = [], []
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op in ("delete", "replace") and i2 - i1 >= min_run:
            only_a.append(" ".join(a[i1:i2]))
        if op in ("insert", "replace") and j2 - j1 >= min_run:
            only_b.append(" ".join(b[j1:j2]))
    return only_a, only_b


@dataclass
class Result:
    source: str
    target: str
    status: str  # match | differs | error
    frontmatter_diff: list[str]
    line_similarity: float
    text_similarity: float
    branch_only_words: int
    converted_only_words: int
    branch_only: list[str]
    converted_only: list[str]
    error: str = ""
    mdx_errors: list[str] = field(default_factory=list)


def compare(source: str, target: Path, ref: str, convert, min_run: int, diff_dir: Path | None,
            ignore_keys: frozenset[str] = frozenset(), out_dir: Path | None = None) -> Result:
    rel_target = str(target.relative_to(ROOT))
    raw = git("show", f"{ref}:{source}")
    try:
        converted = convert(raw, ROOT / source).lstrip("\ufeff")
    except Exception as e:  # noqa: BLE001 - report and continue with the next page
        return Result(source, rel_target, "error", [], 0.0, 0.0, 0, 0, [], [], f"{type(e).__name__}: {e}")

    if out_dir:
        out = out_dir / rel_target
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(converted, encoding="utf-8")
    expected = target.read_text(encoding="utf-8-sig")
    exp_meta, exp_body = split_frontmatter(expected)
    got_meta, got_body = split_frontmatter(converted)
    fm_diff = [
        k for k in sorted(set(exp_meta) | set(got_meta))
        if k not in ignore_keys and exp_meta.get(k) != got_meta.get(k)
    ]

    exp_lines, got_lines = normalize_lines(exp_body), normalize_lines(got_body)
    line_sim = difflib.SequenceMatcher(None, exp_lines, got_lines, autojunk=False).ratio()
    exp_words, got_words = words(exp_body), words(got_body)
    text_sim = difflib.SequenceMatcher(None, exp_words, got_words, autojunk=False).ratio()
    branch_only, converted_only = only_in(exp_words, got_words, min_run)

    status = "match" if exp_lines == got_lines and not fm_diff else "differs"
    if diff_dir and status != "match":
        out = diff_dir / (rel_target + ".diff")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            "".join(
                difflib.unified_diff(
                    normalize_and_join(expected),
                    normalize_and_join(converted),
                    fromfile=f"branch/{rel_target}",
                    tofile=f"converted/{source}",
                )
            ),
            encoding="utf-8",
        )
    return Result(
        source,
        rel_target,
        status,
        fm_diff,
        round(line_sim, 4),
        round(text_sim, 4),
        sum(len(r.split()) for r in branch_only),
        sum(len(r.split()) for r in converted_only),
        branch_only,
        converted_only,
    )


def normalize_and_join(text: str) -> list[str]:
    return [line + "\n" for line in normalize_lines(text)]


def check_mdx(results: list[Result], out_dir: Path, modules: str) -> None:
    """Compile the converted pages with scripts/check_mdx.mjs and record the problems."""
    by_target = {str(out_dir / r.target): r for r in results if r.status != "error"}
    proc = subprocess.run(
        ["node", str(ROOT / "scripts" / "check_mdx.mjs"), "--modules", modules, "--stdin"],
        input="\n".join(by_target), capture_output=True, text=True,
    )
    if proc.returncode not in (0, 1):
        sys.exit(f"check_mdx.mjs failed: {proc.stderr.strip()}")
    for line in proc.stdout.splitlines():
        item = json.loads(line)
        if not item["ok"]:
            by_target[item["file"]].mdx_errors.append(f"{item.get('line')}:{item.get('column')}: {item['message']}")


def load_converter(spec: str):
    module, _, func = spec.partition(":")
    return getattr(importlib.import_module(module), func or "convert")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("paths", nargs="*", help="limit to source paths under these prefixes (e.g. en/applications)")
    parser.add_argument("--ref", default="origin/master", help="git ref holding the Jekyll sources (default: origin/master)")
    parser.add_argument("--since", default="2026-05-01", help="only pages not changed on ref since this date (default: 2026-05-01)")
    parser.add_argument("--all", action="store_true", help="include pages changed after --since")
    parser.add_argument("--converter", default=DEFAULT_CONVERTER, help="module:function taking (source_text, path) (default: existing scripts)")
    parser.add_argument("--ignore-frontmatter", default="description",
                        help="comma-separated frontmatter keys not compared (default: description)")
    parser.add_argument("--min-run", type=int, default=3, help="minimum run of words to report as one-sided text (default: 3)")
    parser.add_argument("--diff-dir", type=Path, help="write a unified diff per differing page here")
    parser.add_argument("--json", type=Path, help="write all results as JSON here")
    parser.add_argument("--mdx-modules", default=os.environ.get("MDX_MODULES"),
                        help="directory with @mdx-js/mdx, remark-gfm and remark-math installed; "
                             "compiles the converted pages (default: $MDX_MODULES)")
    parser.add_argument("--show", type=int, default=30, help="number of worst pages to list (default: 30)")
    args = parser.parse_args()

    convert = load_converter(args.converter)
    dates = last_modified(args.ref)
    sources = sorted(
        s for s in dates
        if re.search(r"\.(html|md)$", s)
        and (not args.paths or any(s.startswith(p.rstrip("/")) for p in args.paths))
        and (args.all or dates[s] < args.since)
    )

    results: list[Result] = []
    skipped_no_target = skipped_redirect = 0
    tmp = tempfile.TemporaryDirectory() if args.mdx_modules else None
    out_dir = Path(tmp.name) if tmp else None
    for source in sources:
        try:
            raw_head = git("show", f"{args.ref}:{source}")
        except subprocess.CalledProcessError:
            continue  # deleted on ref
        if is_redirect_stub(raw_head):
            skipped_redirect += 1
            continue
        target = branch_target(source)
        if target is None:
            skipped_no_target += 1
            continue
        ignore = frozenset(k for k in args.ignore_frontmatter.split(",") if k)
        results.append(compare(source, target, args.ref, convert, args.min_run, args.diff_dir, ignore, out_dir))

    if out_dir:
        check_mdx(results, out_dir, args.mdx_modules)
        tmp.cleanup()

    if args.json:
        args.json.write_text(json.dumps([asdict(r) for r in results], indent=2), encoding="utf-8")

    n = len(results)
    if not n:
        print("No pages to compare.")
        return 1
    matches = sum(r.status == "match" for r in results)
    errors = [r for r in results if r.status == "error"]
    ok = [r for r in results if r.status != "error"]
    print(f"Compared {n} pages from {args.ref} (skipped {skipped_redirect} redirects, {skipped_no_target} without a branch page)")
    print(f"  exact match:           {matches}")
    print(f"  errors:                {len(errors)}")
    if ok:
        print(f"  mean line similarity:  {sum(r.line_similarity for r in ok) / len(ok):.3f}")
        print(f"  mean text similarity:  {sum(r.text_similarity for r in ok) / len(ok):.3f}")
        print(f"  branch-only words:     {sum(r.branch_only_words for r in ok)}")
        print(f"  converted-only words:  {sum(r.converted_only_words for r in ok)}")
    if out_dir:
        invalid = [r for r in ok if r.mdx_errors]
        print(f"  invalid MDX:           {len(invalid)}")
        for r in invalid:
            print(f"INVALID {r.target}: {r.mdx_errors[0]}" + (f" (+{len(r.mdx_errors) - 1} more)" if len(r.mdx_errors) > 1 else ""))

    for r in errors:
        print(f"ERROR {r.source}: {r.error}")

    worst = sorted((r for r in ok if r.status != "match"), key=lambda r: (r.text_similarity, r.line_similarity))
    if worst and args.show:
        print(f"\nWorst {min(args.show, len(worst))} pages (text / line similarity, one-sided words branch/converted):")
        for r in worst[: args.show]:
            print(f"  {r.text_similarity:.3f} {r.line_similarity:.3f}  {r.branch_only_words:5d}/{r.converted_only_words:<5d} {r.target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
