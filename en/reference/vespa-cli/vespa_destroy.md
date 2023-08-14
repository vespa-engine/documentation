---
render_with_liquid: false
---

## vespa destroy

Remove a deployed application and its data

### Synopsis

Remove a deployed application and its data.

This command removes the currently deployed application and permanently
deletes its data.

When run interactively, the command will prompt for confirmation before
removing the application. When run non-interactively, the command will refuse
to remove the application unless the --force option is given.

This command cannot be used to remove production deployments in Vespa Cloud. See
https://cloud.vespa.ai/en/deleting-applications for how to remove production
deployments.


```
vespa destroy [flags]
```

### Examples

```
$ vespa destroy
$ vespa destroy -a mytenant.myapp.myinstance
$ vespa destroy --force
```

### Options

```
      --force   Disable confirmation (default false)
  -h, --help    help for destroy
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

