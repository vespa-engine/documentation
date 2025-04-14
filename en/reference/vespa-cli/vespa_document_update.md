---
title: vespa document update
render_with_liquid: false
---

## vespa document update

Modifies some fields of an existing document

### Synopsis

Updates the values of the fields given in a json file as specified in the file.
If the document id is specified both as an argument and in the file the argument takes precedence.

```
vespa document update [id] json-file [flags]
```

### Examples

```
$ vespa document update src/test/resources/A-Head-Full-of-Dreams-Update.json
$ vespa document update id:mynamespace:music::a-head-full-of-dreams src/test/resources/A-Head-Full-of-Dreams.json
$ vespa document --data '{"update": "id:mynamespace:music::a-head-full-of-dreams", "fields": {"title": {"assign": "The best of Bob Dylan"}}}'
```

### Options

```
  -d, --data string      Document data to use instead of reading from file or stdin
      --header strings   Add a header to the HTTP request, on the format 'Header: Value'. This can be specified multiple times
  -h, --help             help for update
  -T, --timeout int      Timeout for the document request in seconds (default 60)
  -v, --verbose          Print the equivalent curl command for the document operation
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

* [vespa document](vespa_document.html)	 - Issue a single document operation to Vespa
