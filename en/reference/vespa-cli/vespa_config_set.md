---
title: vespa config set
render_with_liquid: false
---

## vespa config set

Set a configuration option.

```
vespa config set option-name value [flags]
```

### Examples

```
# Set the target to Vespa Cloud
$ vespa config set target cloud

# Set application, without a specific instance. The instance will be named "default"
$ vespa config set application my-tenant.my-application

# Set application with a specific instance
$ vespa config set application my-tenant.my-application.my-instance

# Set the instance explicitly. This will take precedence over an instance specified as part of the application option.
$ vespa config set instance other-instance

# Set an option in local configuration, for the current application only
$ vespa config set --local zone perf.us-north-1
```

### Options

```
  -h, --help    help for set
  -l, --local   Write option to local configuration, i.e. for the current application
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

* [vespa config](vespa_config.html)	 - Manage persistent values for global flags

