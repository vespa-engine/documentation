---
title: vespa status endpoint
render_with_liquid: false
---

## vespa status endpoint

Show Vespa endpoints without checking their status

### Synopsis

Show Vespa endpoints without checking their status.

This command shows the current endpoints of a deployed Vespa application,
discovered from the control plane, without contacting the data plane to check
their status. This is useful when you only have control plane credentials.

This is equivalent to: vespa status --no-verify

```
vespa status endpoint [flags]
```

### Examples

```
$ vespa status endpoint
$ vespa status endpoint --cluster mycluster
$ vespa status endpoint --format plain
```

### Options

```
      --format string   Output format. Must be 'human' (human-readable), 'plain' (cluster URL only), or 'json' (default "human")
  -h, --help            help for endpoint
  -w, --wait int        Number of seconds to wait for service(s) to become ready. 0 to disable (default 0)
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

* [vespa status](vespa_status.html)	 - Show Vespa endpoints and status

