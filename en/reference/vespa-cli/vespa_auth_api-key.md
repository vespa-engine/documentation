---
render_with_liquid: false
---

## vespa auth api-key

Create a new user API key for control-plane authentication with Vespa Cloud

### Synopsis

Create a new user API key for control-plane authentication with Vespa Cloud.

The API key will be stored in the Vespa CLI home directory
(see 'vespa help config'). Other commands will then automatically load the API
key as necessary.

It's possible to override the API key used through environment variables. This
can be useful in continuous integration systems.

Example of setting the key in-line:

    export VESPA_CLI_API_KEY="my api key"

Example of loading the key from a custom path:

    export VESPA_CLI_API_KEY_FILE=/path/to/api-key

Note that when overriding API key through environment variables, that key will
always be used. It's not possible to specify a tenant-specific key.

Read more in https://cloud.vespa.ai/en/security/guide

```
vespa auth api-key [flags]
```

### Examples

```
$ vespa auth api-key -a my-tenant.my-app.my-instance
```

### Options

```
  -f, --force   Force overwrite of existing API key
  -h, --help    help for api-key
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

