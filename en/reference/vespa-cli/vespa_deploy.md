---
title: vespa deploy
render_with_liquid: false
---

## vespa deploy

Deploy (prepare and activate) an application package

### Synopsis

Deploy (prepare and activate) an application package.

When this returns successfully the application package has been validated
and activated on config servers. The process of applying it on individual nodes
has started but may not have completed.

If application directory is not specified, it defaults to working directory.

When deploying to Vespa Cloud the system can be overridden by setting the
environment variable VESPA_CLI_CLOUD_SYSTEM. This is intended for internal use
only.

In Vespa Cloud you may override the Vespa runtime version for your deployment.
This option should only be used if you have a reason for using a specific
version. By default Vespa Cloud chooses a suitable version for you.


```
vespa deploy [application-directory-or-file] [flags]
```

### Examples

```
$ vespa deploy .
$ vespa deploy -t cloud
$ vespa deploy -t cloud -z dev.aws-us-east-1c  # -z can be omitted here as this zone is the default
$ vespa deploy -t cloud -z perf.aws-us-east-1c
```

### Options

```
  -A, --add-cert           Copy certificate of the configured application to the current application package
  -h, --help               help for deploy
  -l, --log-level string   Log level for Vespa logs. Must be "error", "warning", "info" or "debug" (default "error")
  -V, --version string     Override the Vespa runtime version to use in Vespa Cloud
  -w, --wait int           Number of seconds to wait for service(s) to become ready. 0 to disable (default 60)
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

