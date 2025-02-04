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
$ vespa query "yql=select * from music where album contains 'head'" hits=5
$ vespa query --format=plain "yql=select * from music where album contains 'head'" hits=5
$ vespa query --header="X-First-Name: Joe" "yql=select * from music where album contains 'head'" hits=5
```

### Options

```
      --file string      Read query parameters from the given JSON file and send a POST request, with overrides from arguments
      --format string    Output format. Must be 'human' (human-readable) or 'plain' (no formatting) (default "human")
      --header strings   Add a header to the HTTP request, on the format 'Header: Value'. This can be specified multiple times
  -h, --help             help for query
  -T, --timeout int      Timeout for the query in seconds (default 10)
  -v, --verbose          Print the equivalent curl command for the query
  -w, --wait int         Number of seconds to wait for service(s) to become ready. 0 to disable (default 0)
```

### Options inherited from parent commands

```
  -a, --application string   The application to use (cloud only). Format "tenant.application.instance" - instance is optional
  -C, --cluster string       The container cluster to use. This is only required for applications with multiple clusters
  -c, --color string         Whether to use colors in output. Must be "auto", "never", or "always" (default "auto")
  -i, --instance string      The instance of the application to use (cloud only)
  -q, --quiet                Print only errors
  -t, --target string        The target platform to use. Must be "local", "cloud", "hosted" or an URL (default "local")
  -z, --zone string          The zone to use. This defaults to a dev zone (cloud only)
```

### SEE ALSO

* [vespa](vespa.html)	 - The command-line tool for Vespa.ai

