#!/usr/bin/env python3
"""Update languages/vespa-schema.json from the Vespa schema TextMate grammar.

The grammar is generated in vespa-engine/vespa (integration/tmgrammar) from the same
source as the schema language server. Mintlify highlights code with Shiki, which uses
the grammar's "name" as the language id, so the copy here is named "vespa-schema"
(with "sd" as an alias) for use in code fences: ```vespa-schema

Usage:
    scripts/update_schema_grammar.py            # latest on master
    scripts/update_schema_grammar.py --ref SHA
"""

from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path

UPSTREAM = "https://raw.githubusercontent.com/vespa-engine/vespa/{ref}/integration/tmgrammar/grammars/vespa-schema.tmLanguage.json"
OUT = Path(__file__).resolve().parent.parent / "languages" / "vespa-schema.json"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--ref", default="master", help="vespa-engine/vespa commit or branch (default: master)")
    args = parser.parse_args()
    with urllib.request.urlopen(UPSTREAM.format(ref=args.ref)) as r:
        grammar = json.load(r)
    out = {"$schema": grammar["$schema"], "name": "vespa-schema", "displayName": grammar["name"], "aliases": ["sd"]}
    out.update({k: v for k, v in grammar.items() if k not in ("$schema", "name")})
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {OUT.relative_to(OUT.parent.parent)} from vespa-engine/vespa@{args.ref}")


if __name__ == "__main__":
    main()
