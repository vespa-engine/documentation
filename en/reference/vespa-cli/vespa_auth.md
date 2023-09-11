---
title: vespa auth
render_with_liquid: false
---

## vespa auth

Manage Vespa Cloud credentials

### Synopsis

Manage Vespa Cloud credentials.

```
vespa auth [flags]
```

### Options

```
  -h, --help   help for auth
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
* [vespa auth api-key](vespa_auth_api-key.html)	 - Create a new user API key for control-plane authentication with Vespa Cloud
* [vespa auth cert](vespa_auth_cert.html)	 - Create a new private key and self-signed certificate for data-plane access with Vespa Cloud
* [vespa auth login](vespa_auth_login.html)	 - Authenticate Vespa CLI with Vespa Cloud
* [vespa auth logout](vespa_auth_logout.html)	 - Sign out of Vespa Cloud

