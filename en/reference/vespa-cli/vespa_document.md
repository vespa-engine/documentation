---
title: vespa document
render_with_liquid: false
---

## vespa document

Issue a single document operation to Vespa

### Synopsis

Issue a single document operation to Vespa.

The operation must be on the format documented in
[https://docs.vespa.ai/en/reference/document-json-format.html#document-operations](https://docs.vespa.ai/en/reference/document-json-format.html#document-operations)

When this returns successfully, the document is guaranteed to be visible in any
subsequent get or query operation.

To feed with high throughput, [https://docs.vespa.ai/en/reference/vespa-cli/vespa_feed.html](https://docs.vespa.ai/en/reference/vespa-cli/vespa_feed.html)
should be used instead of this.

```
vespa document json-file [flags]
```

### Examples

```
$ vespa document src/test/resources/A-Head-Full-of-Dreams.json
```

### Options

```
      --header strings   Add a header to the HTTP request, on the format 'Header: Value'. This can be specified multiple times
  -h, --help             help for document
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

* [vespa](vespa.html)	 - The command-line tool for Vespa.ai
* [vespa document get](vespa_document_get.html)	 - Gets a document
* [vespa document put](vespa_document_put.html)	 - Writes a document to Vespa
* [vespa document remove](vespa_document_remove.html)	 - Removes a document from Vespa
* [vespa document update](vespa_document_update.html)	 - Modifies some fields of an existing document

