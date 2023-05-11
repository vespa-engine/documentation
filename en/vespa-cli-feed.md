---
# Copyright Yahoo. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "Feeding with Vespa CLI"
---

[Vespa CLI](/en/vespa-cli.html) provides a high performance feed client through
its `feed` command. The client feeds documents concurrently, with retries and
dynamic throttling.

- The input files for the `feed` command are expected to contain either a JSON
  array of feed operations, or one JSON operation per line
  ([JSONL](https://jsonlines.org/)).

- `vespa feed` uses the
  [Document API](/en/reference/services-container.html#document-api), which must
  be enabled in the container before documents can be fed.

## Examples

Feed documents from files or standard in:

```
$ vespa feed docs1.json docs2.json
$ cat docs.json | vespa feed -
```

Display a periodic summary (every 3 seconds) while feeding:

```
$ vespa feed --progress=3 docs.json
```

Print successful operations:

```
$ vespa feed --verbose docs.json
```

Copy documents from one cluster to another:

```
vespa visit --target http://localhost:8080 | vespa feed --target http://localhost:9090 -
```

See `vespa help feed` or `man vespa-feed` for complete usage.
