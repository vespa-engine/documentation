---
title: vespa status deploy
render_with_liquid: false
---

## vespa status deploy

Verify that the deploy service is ready to use

```
vespa status deploy [flags]
```

### Examples

```
$ vespa status deploy
```

### Options

```
  -h, --help       help for deploy
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

* [vespa status](vespa_status.html)	 - Verify that a service is ready to use (query by default)

