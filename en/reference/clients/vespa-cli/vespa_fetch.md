---
title: vespa fetch
render_with_liquid: false
---

## vespa fetch

Download a deployed application package

### Synopsis

Download a deployed application package.

This command can be used to download an already deployed Vespa application
package. The package is written as a ZIP file to the given path, or current
directory if no path is given.

```
vespa fetch [path] [flags]
```

### Examples

```
$ vespa fetch
$ vespa fetch mydir/
$ vespa fetch -t cloud mycloudapp.zip

```

### Options

```
  -h, --help   help for fetch
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

* [vespa](vespa.html)	 - The command-line tool for Vespa.ai

