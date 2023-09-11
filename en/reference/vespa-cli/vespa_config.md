---
title: vespa config
render_with_liquid: false
---

## vespa config

Configure persistent values for global flags

### Synopsis

Configure persistent values for global flags.

This command allows setting persistent values for global flags. On future
invocations the flag can then be omitted as it is read from the config file
instead.

Configuration is written to $HOME/.vespa by default. This path can be
overridden by setting the VESPA_CLI_HOME environment variable.

When setting an option locally, the configuration is written to .vespa in the
working directory, where that directory is assumed to be a Vespa application
directory. This allows you have separate configuration options per application.

Vespa CLI chooses the value for a given option in the following order, from
most to least preferred:

1. Flag value specified on the command line
2. Local config value
3. Global config value
4. Default value

The following global flags/options can be configured:

application

Specifies the application ID to manage. It has three parts, separated by
dots, with the third part being optional. This is only relevant for the "cloud"
and "hosted" targets. See [https://cloud.vespa.ai/en/tenant-apps-instances](https://cloud.vespa.ai/en/tenant-apps-instances) for
more details. This has no default value. Examples: tenant1.app1,
tenant1.app1.instance1

cluster

Specifies the container cluster to manage. If left empty (default) and the
application has only one container cluster, that cluster is chosen
automatically. When an application has multiple cluster this must be set a
valid cluster name, as specified in services.xml. See
[https://docs.vespa.ai/en/reference/services-container.html](https://docs.vespa.ai/en/reference/services-container.html) for more details.

color

Controls how Vespa CLI uses colors. Setting this to "auto" (default) enables
colors if supported by the terminal, "never" completely disables colors and
"always" enables colors unilaterally.

instance

Specifies the instance of the application to manage. When specified, this takes
precedence over the instance specified as part of application. This has no
default value. Example: instance2

quiet

Print only errors.

target

Specifies the target to use for commands that interact with a Vespa platform,
e.g. vespa deploy or vespa query. Possible values are:

- local: (default) Connect to a Vespa platform running at localhost
- cloud: Connect to Vespa Cloud
- hosted: Connect to hosted Vespa (internal platform)
- *url*: Connect to a platform running at given URL.

zone

Specifies a custom dev or perf zone to use when connecting to a Vespa platform.
This is only relevant for cloud and hosted targets. By default, a zone is
chosen automatically. See [https://cloud.vespa.ai/en/reference/zones](https://cloud.vespa.ai/en/reference/zones) for
available zones. Examples: dev.aws-us-east-1c, perf.aws-us-east-1c


```
vespa config [flags]
```

### Options

```
  -h, --help   help for config
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
* [vespa config get](vespa_config_get.html)	 - Show given configuration option, or all configuration options
* [vespa config set](vespa_config_set.html)	 - Set a configuration option.
* [vespa config unset](vespa_config_unset.html)	 - Unset a configuration option.

