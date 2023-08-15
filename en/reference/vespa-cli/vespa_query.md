---
title: vespa query
render_with_liquid: false
---

## vespa query

Issue a query to Vespa

### Synopsis

Issue a query to Vespa.

Any parameter from [https://docs.vespa.ai/en/reference/query-api-reference.html](https://docs.vespa.ai/en/reference/query-api-reference.html)
can be set by the syntax [parameter-name]=[value].

```
vespa query query-parameters [flags]
```

### Examples

```
$ vespa query "yql=select * from music where album contains 'head';" hits=5
```

### Options

```
  -h, --help          help for query
  -T, --timeout int   Timeout for the query in seconds (default 10)
  -v, --verbose       Print the equivalent curl command for the query
  -w, --wait int      Number of seconds to wait for a service to become ready. 0 to disable (default 0)
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

