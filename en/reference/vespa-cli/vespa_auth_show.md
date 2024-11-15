---
title: vespa auth show
render_with_liquid: false
---

## vespa auth show

Show authenticated user

### Synopsis

Show which user (if any) is authenticated with "auth login"


```
vespa auth show [flags]
```

### Examples

```
$ vespa auth show
```

### Options

```
  -h, --help   help for show
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

* [vespa auth](vespa_auth.html)	 - Manage Vespa Cloud credentials

