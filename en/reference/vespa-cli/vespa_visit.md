---
title: vespa visit
render_with_liquid: false
---

## vespa visit

Visit and print all documents in a Vespa cluster

### Synopsis

Visit and print all documents in a Vespa cluster.

By default prints each document received on its own line (JSONL format).


```
vespa visit [flags]
```

### Examples

```
$ vespa visit # get documents from any cluster
$ vespa visit --content-cluster search # get documents from cluster named "search"
$ vespa visit --field-set "[id]" # list document IDs

```

### Options

```
      --bucket-space strings     The "default" or "global" bucket space (default [global,default])
      --chunk-count int          Chunk by count (default 1000)
      --content-cluster string   Which content cluster to visit documents from (default "*")
      --debug-mode               Print debugging output
      --field-set string         Which fieldset to ask for
      --from string              Timestamp to visit from, in seconds
  -h, --help                     help for visit
      --json-lines               Output documents as JSON lines (default true)
      --make-feed                Output JSON array suitable for vespa-feeder
      --pretty-json              Format pretty JSON
      --selection string         Select subset of cluster
      --slice-id int             The number of the slice this visit invocation should fetch (default -1)
      --slices int               Split the document corpus into this number of independent slices (default -1)
      --to string                Timestamp to visit up to, in seconds
  -w, --wait int                 Number of seconds to wait for a service to become ready. 0 to disable (default 0)
```

### Options inherited from parent commands

```
  -a, --application string   The application to use
  -C, --cluster string       The container cluster to use. This is only required for applications with multiple clusters
  -c, --color string         Whether to use colors in output. Must be "auto", "never", or "always" (default "auto")
  -i, --instance string      The instance of the application to use
  -q, --quiet                Print only errors
  -t, --target string        The target platform to use. Must be "local", "cloud", "hosted" or an URL (default "local")
  -z, --zone string          The zone to use. This defaults to a dev zone
```

### SEE ALSO

* [vespa](vespa.html)	 - The command-line tool for Vespa.ai

