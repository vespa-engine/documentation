---
title: vespa prod
render_with_liquid: false
---

## vespa prod

Deploy an application package to production in Vespa Cloud

### Synopsis

Deploy an application package to production in Vespa Cloud.

Configure and deploy your application package to production in Vespa Cloud.

```
vespa prod [flags]
```

### Examples

```
$ vespa prod init
$ vespa prod deploy
```

### Options

```
  -h, --help   help for prod
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
* [vespa prod deploy](vespa_prod_deploy.html)	 - Deploy an application to production
* [vespa prod init](vespa_prod_init.html)	 - Modify service.xml and deployment.xml for production deployment

