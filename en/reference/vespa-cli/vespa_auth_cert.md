---
title: vespa auth cert
render_with_liquid: false
---

## vespa auth cert

Create a new private key and self-signed certificate for data-plane access with Vespa Cloud

### Synopsis

Create a new private key and self-signed certificate for data-plane access with Vespa Cloud.

The private key and certificate will be stored in the Vespa CLI home directory
(see 'vespa help config'). Other commands will then automatically load the
certificate as necessary. The certificate will be added to your application
package specified as an argument to this command (default '.').

It's possible to override the private key and certificate used through
environment variables. This can be useful in continuous integration systems.

It's also possible override the CA certificate which can be useful when using self-signed certificates with a
self-hosted Vespa service. See [https://docs.vespa.ai/en/mtls.html](https://docs.vespa.ai/en/mtls.html) for more information.

Example of setting the CA certificate, certificate and key in-line:

    export VESPA_CLI_DATA_PLANE_CA_CERT="my CA cert"
    export VESPA_CLI_DATA_PLANE_CERT="my cert"
    export VESPA_CLI_DATA_PLANE_KEY="my private key"

Example of loading CA certificate, certificate and key from custom paths:

    export VESPA_CLI_DATA_PLANE_CA_CERT_FILE=/path/to/cacert
    export VESPA_CLI_DATA_PLANE_CERT_FILE=/path/to/cert
    export VESPA_CLI_DATA_PLANE_KEY_FILE=/path/to/key

Note that when overriding key pair through environment variables, that key pair
will always be used for all applications. It's not possible to specify an
application-specific key.

Read more in [https://cloud.vespa.ai/en/security/guide](https://cloud.vespa.ai/en/security/guide)

```
vespa auth cert [flags]
```

### Examples

```
$ vespa auth cert -a my-tenant.my-app.my-instance
$ vespa auth cert -a my-tenant.my-app.my-instance path/to/application/package
```

### Options

```
  -f, --force    Force overwrite of existing certificate and private key
  -h, --help     help for cert
  -N, --no-add   Do not add certificate to the application package
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

* [vespa auth](vespa_auth.html)	 - Manage Vespa Cloud credentials
* [vespa auth cert add](vespa_auth_cert_add.html)	 - Add certificate to application package

