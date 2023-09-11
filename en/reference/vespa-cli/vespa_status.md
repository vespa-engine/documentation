---
title: vespa status
render_with_liquid: false
---

## vespa status

Verify that container service(s) are ready to use

```
vespa status [flags]
```

### Examples

```
$ vespa status
$ vespa status --cluster mycluster
```

### Options

```
  -h, --help       help for status
  -w, --wait int   Number of seconds to wait for service(s) to become ready. 0 to disable (default 0)
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
* [vespa status deploy](vespa_status_deploy.html)	 - Verify that the deploy service is ready to use
* [vespa status deployment](vespa_status_deployment.html)	 - Verify that deployment has converged on latest, or given, ID

