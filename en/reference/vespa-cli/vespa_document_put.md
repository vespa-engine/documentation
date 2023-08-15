---
title: vespa document put
render_with_liquid: false
---

## vespa document put

Writes a document to Vespa

### Synopsis

Writes the document in the given file to Vespa.
If the document already exists, all its values will be replaced by this document.
If the document id is specified both as an argument and in the file the argument takes precedence.

```
vespa document put [id] json-file [flags]
```

### Examples

```
$ vespa document put src/test/resources/A-Head-Full-of-Dreams.json
$ vespa document put id:mynamespace:music::a-head-full-of-dreams src/test/resources/A-Head-Full-of-Dreams.json
```

### Options

```
  -h, --help          help for put
  -T, --timeout int   Timeout for the document request in seconds (default 60)
  -v, --verbose       Print the equivalent curl command for the document operation
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

* [vespa document](vespa_document.html)	 - Issue a single document operation to Vespa

