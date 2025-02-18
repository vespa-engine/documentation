---
title: vespa document get
render_with_liquid: false
---

## vespa document get

Gets one or more documents

```
vespa document get id(s) [flags]
```

### Examples

```
$ vespa document get id:mynamespace:music::song-1
$ vespa document get id:mynamespace:music::song-1 id:mynamespace:music::song-2
```

### Options

```
      --field-set string   Fields to include when reading document
      --header strings     Add a header to the HTTP request, on the format 'Header: Value'. This can be specified multiple times
  -h, --help               help for get
      --ignore-missing     Do not treat non-existent document as an error
  -T, --timeout int        Timeout for the document request in seconds (default 60)
  -v, --verbose            Print the equivalent curl command for the document operation
  -w, --wait int           Number of seconds to wait for service(s) to become ready. 0 to disable (default 0)
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

* [vespa document](vespa_document.html)	 - Issue a single document operation to Vespa

