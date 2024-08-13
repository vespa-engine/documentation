---
title: vespa status deploy
render_with_liquid: false
---

## vespa status deploy

Show status of the Vespa deploy service

```
vespa status deploy [flags]
```

### Examples

```
$ vespa status deploy
```

### Options

```
      --format string   Output format. Must be 'human' (human-readable text) or 'plain' (cluster URL only) (default "human")
  -h, --help            help for deploy
  -w, --wait int        Number of seconds to wait for service(s) to become ready. 0 to disable (default 0)
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

* [vespa status](vespa_status.html)	 - Show Vespa endpoints and status

