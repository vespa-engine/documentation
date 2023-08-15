---
title: vespa auth cert add
render_with_liquid: false
---

## vespa auth cert add

Add certificate to application package

### Synopsis

Add an existing self-signed certificate for Vespa Cloud deployment to your application package.

The certificate will be loaded from the Vespa CLI home directory (see 'vespa
help config') by default.

The location of the application package can be specified as an argument to this
command (default '.').

```
vespa auth cert add [flags]
```

### Examples

```
$ vespa auth cert add -a my-tenant.my-app.my-instance
$ vespa auth cert add -a my-tenant.my-app.my-instance path/to/application/package
```

### Options

```
  -f, --force   Force overwrite of existing certificate
  -h, --help    help for add
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

* [vespa auth cert](vespa_auth_cert.html)	 - Create a new private key and self-signed certificate for data-plane access with Vespa Cloud

