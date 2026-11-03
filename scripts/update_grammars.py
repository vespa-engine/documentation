#!/usr/bin/env python3
"""Update the syntax highlighting grammars in languages/ from vespa-engine/vespa.

The Vespa TextMate grammars are generated in vespa-engine/vespa (integration/tmgrammar).
Mintlify highlights code with Shiki, which uses a grammar's "name" as the language id in
code fences, so the copies here are renamed:

    languages/vespa-schema.json              ```vespa-schema  (aliases: sd, vespa-schema-language)
    languages/vespa-yql.json                 ```vespa-yql     (alias: yql)
    languages/vespa-ranking-expression.json  ```vespa-ranking-expression

vespa-ranking-expression is the schema grammar starting at its ranking-expression rule, for
an expression on its own, as the Jekyll site's _plugins/rouge_textmate.rb does.
The grammars must be listed under styling.codeblocks.languages.custom in docs.json.

Usage:
    scripts/update_grammars.py            # latest on master
    scripts/update_grammars.py --ref SHA
"""

from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path

UPSTREAM = "https://raw.githubusercontent.com/vespa-engine/vespa/{ref}/integration/tmgrammar/grammars/{name}.tmLanguage.json"
OUT = Path(__file__).resolve().parent.parent / "languages"


def fetch(name: str, ref: str) -> dict:
    with urllib.request.urlopen(UPSTREAM.format(ref=ref, name=name)) as r:
        return json.load(r)


def renamed(grammar: dict, name: str, aliases: list[str], **overrides) -> dict:
    out = {"$schema": grammar["$schema"], "name": name, "displayName": overrides.pop("displayName", grammar["name"])}
    if aliases:
        out["aliases"] = aliases
    out.update({k: v for k, v in grammar.items() if k not in ("$schema", "name")})
    out.update(overrides)
    return out


def write(grammar: dict) -> None:
    path = OUT / f"{grammar['name']}.json"
    path.write_text(json.dumps(grammar, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {path.relative_to(OUT.parent)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--ref", default="master", help="vespa-engine/vespa commit or branch (default: master)")
    args = parser.parse_args()
    OUT.mkdir(exist_ok=True)

    schema = fetch("vespa-schema", args.ref)
    write(renamed(schema, "vespa-schema", ["sd", "vespa-schema-language"]))
    write(renamed(fetch("vespa-yql", args.ref), "vespa-yql", ["yql"]))
    assert "ranking-expression" in schema["repository"], "the schema grammar has no ranking-expression rule"
    write(renamed(schema, "vespa-ranking-expression", [], displayName="Vespa ranking expression",
                  scopeName="source.vespaRankingExpression", patterns=[{"include": "#ranking-expression"}]))
    print(f"from vespa-engine/vespa@{args.ref}")


if __name__ == "__main__":
    main()
