---
title: vespa status deployment
render_with_liquid: false
---

## vespa status deployment

Verify that deployment has converged on latest, or given, ID

```
vespa status deployment [flags]
```

### Examples

```
$ vespa status deployment
$ vespa status deployment -t cloud [run-id]
$ vespa status deployment -t local [session-id]

```

### Options

```
  -h, --help       help for deployment
  -w, --wait int   Number of seconds to wait for service(s) to become ready. 0 to disable (default 0)
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

* [vespa status](vespa_status.html)	 - Verify that container service(s) are ready to use

