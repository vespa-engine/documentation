---
title: vespa document get
render_with_liquid: false
---

## vespa document get

Gets a document

```
vespa document get id [flags]
```

### Examples

```
$ vespa document get id:mynamespace:music::a-head-full-of-dreams
```

### Options

```
  -h, --help          help for get
  -T, --timeout int   Timeout for the document request in seconds (default 60)
  -v, --verbose       Print the equivalent curl command for the document operation
  -w, --wait int      Number of seconds to wait for service(s) to become ready. 0 to disable (default 0)
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

* [vespa document](vespa_document.html)	 - Issue a single document operation to Vespa

