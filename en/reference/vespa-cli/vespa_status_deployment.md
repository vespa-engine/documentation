---
title: vespa status deployment
render_with_liquid: false
---

## vespa status deployment

Show status of a Vespa deployment

### Synopsis

Show status of a Vespa deployment.

This commands shows whether a Vespa deployment has converged on the latest run
(Vespa Cloud) or config generation (self-hosted). If an argument is given,
show the convergence status of that particular run or generation.


```
vespa status deployment [flags]
```

### Examples

```
$ vespa status deployment
$ vespa status deployment -t cloud [run-id]
$ vespa status deployment -t local [session-id]
$ vespa status deployment -t local [session-id] --wait 600

```

### Options

```
  -h, --help       help for deployment
  -w, --wait int   Number of seconds to wait for service(s) to become ready. 0 to disable (default 0)
```

### Options inherited from parent commands

```
  -a, --application string   The application to use (cloud only)
  -C, --cluster string       The container cluster to use. This is only required for applications with multiple clusters
  -c, --color string         Whether to use colors in output. Must be "auto", "never", or "always" (default "auto")
      --format string        Output format. Must be 'human' (human-readable) or 'plain' (cluster URL only) (default "human")
  -i, --instance string      The instance of the application to use (cloud only)
  -q, --quiet                Print only errors
  -t, --target string        The target platform to use. Must be "local", "cloud", "hosted" or an URL (default "local")
  -z, --zone string          The zone to use. This defaults to a dev zone (cloud only)
```

### SEE ALSO

* [vespa status](vespa_status.html)	 - Show Vespa endpoints and status

