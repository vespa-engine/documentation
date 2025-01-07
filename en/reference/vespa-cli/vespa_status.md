---
title: vespa status
render_with_liquid: false
---

## vespa status

Show Vespa endpoints and status

### Synopsis

Show Vespa endpoints and status.

This command shows the current endpoints, and their status, of a deployed Vespa
application.

```
vespa status [flags]
```

### Examples

```
$ vespa status
$ vespa status --cluster mycluster
$ vespa status --cluster mycluster --wait 600
$ vepsa status --format plain --cluster mycluster
```

### Options

```
      --format string   Output format. Must be 'human' (human-readable) or 'plain' (cluster URL only) (default "human")
  -h, --help            help for status
  -w, --wait int        Number of seconds to wait for service(s) to become ready. 0 to disable (default 0)
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
* [vespa status deploy](vespa_status_deploy.html)	 - Show status of the Vespa deploy service
* [vespa status deployment](vespa_status_deployment.html)	 - Show status of a Vespa deployment

