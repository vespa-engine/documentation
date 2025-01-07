---
title: vespa config unset
render_with_liquid: false
---

## vespa config unset

Unset a configuration option.

### Synopsis

Unset a configuration option.

Unsetting a configuration option will reset it to its default value, which may be empty.


```
vespa config unset option-name [flags]
```

### Examples

```
# Reset target to its default value
$ vespa config unset target

# Stop overriding application option in local config
$ vespa config unset --local application
```

### Options

```
  -h, --help    help for unset
  -l, --local   Unset option in local configuration, i.e. for the current application
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

