---
title: vespa feed
render_with_liquid: false
---

## vespa feed

Feed multiple document operations to Vespa

### Synopsis

Feed multiple document operations to Vespa.

This command can be used to feed large amounts of documents to a Vespa cluster
efficiently.

The contents of JSON-FILE must be either a JSON array or JSON objects separated by
newline (JSONL).

If JSON-FILE is a single dash ('-'), documents will be read from standard input.


```
vespa feed json-file [json-file]... [flags]
```

### Examples

```
$ vespa feed docs.jsonl moredocs.json
$ cat docs.jsonl | vespa feed -
```

### Options

```
      --compression string       Compression mode to use. Default is "auto" which compresses large documents. Must be "auto", "gzip" or "none" (default "auto")
      --connections int          The number of connections to use (default 8)
      --deadline int             Exit if this number of seconds elapse without any successful operations. 0 to disable (default 0)
  -h, --help                     help for feed
      --progress int             Print stats summary at given interval, in seconds. 0 to disable (default 0)
      --route string             Target Vespa route for feed operations (default "default")
      --speedtest int            Perform a network speed test using given payload, in bytes. 0 to disable (default 0)
      --speedtest-duration int   Duration of speedtest, in seconds (default 60)
      --timeout int              Individual feed operation timeout in seconds. 0 to disable (default 0)
      --trace int                Network traffic trace level in the range [0,9]. 0 to disable (default 0)
      --verbose                  Verbose mode. Print successful operations in addition to errors
  -w, --wait int                 Number of seconds to wait for service(s) to become ready. 0 to disable (default 0)
```

### Options inherited from parent commands

```
  -a, --application string   The application to use (cloud only)
  -C, --cluster string       The container cluster to use. This is only required for applications with multiple clusters
  -c, --color string         Whether to use colors in output. Must be "auto", "never", or "always" (default "auto")
  -i, --instance string      The instance of the application to use (cloud only)
  -q, --quiet                Print only errors
  -t, --target string        The target platform to use. Must be "local", "cloud", "hosted" or an URL (default "local")
  -z, --zone string          The zone to use. This defaults to a dev zone (cloud only)
```

### SEE ALSO

* [vespa](vespa.html)	 - The command-line tool for Vespa.ai

