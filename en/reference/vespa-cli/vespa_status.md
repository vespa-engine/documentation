---
render_with_liquid: false
---

## vespa status

Verify that a service is ready to use (query by default)

```
vespa status [flags]
```

### Examples

```
$ vespa status query
```

### Options

```
  -h, --help       help for status
  -w, --wait int   Number of seconds to wait for a service to become ready. 0 to disable (default 0)
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
* [vespa status deploy](vespa_status_deploy.html)	 - Verify that the deploy service is ready to use
* [vespa status document](vespa_status_document.html)	 - Verify that the document service is ready to use
* [vespa status query](vespa_status_query.html)	 - Verify that the query service is ready to use (default)

