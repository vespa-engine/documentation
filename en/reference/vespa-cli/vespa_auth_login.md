---
title: vespa auth login
render_with_liquid: false
---

## vespa auth login

Authenticate Vespa CLI with Vespa Cloud control plane. This is preferred over api-key for interactive use

### Synopsis

Authenticate Vespa CLI with Vespa Cloud control plane. This is preferred over api-key for interactive use.

This command runs a browser-based authentication flow for the Vespa Cloud control plane.


```
vespa auth login [flags]
```

### Examples

```
$ vespa auth login
```

### Options

```
  -h, --help   help for login
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

* [vespa auth](vespa_auth.html)	 - Manage Vespa Cloud credentials

