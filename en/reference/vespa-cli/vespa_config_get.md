---
title: vespa config get
render_with_liquid: false
---

## vespa config get

Show given configuration option, or all configuration options

### Synopsis

Show given configuration option, or all configuration options.

By default this command prints the effective configuration for the current
application, i.e. it takes into account any local configuration located in
[working-directory]/.vespa.


```
vespa config get [option-name] [flags]
```

### Examples

```
$ vespa config get
$ vespa config get target
$ vespa config get --local

```

### Options

```
  -h, --help    help for get
  -l, --local   Show only local configuration, if any
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

* [vespa config](vespa_config.html)	 - Configure persistent values for global flags

